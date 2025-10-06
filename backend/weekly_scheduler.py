import os
import asyncio
import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from models import WeeklyCrawlSchedule, EsercenteSocialMapping, BrightDataJob
from brightdata_service import brightdata_service

logger = logging.getLogger(__name__)

class WeeklyCrawlScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Weekly crawl scheduler started")
    
    def schedule_weekly_crawls(self):
        """
        Schedula i crawl settimanali per ogni lunedì alle 9:00
        """
        self.scheduler.add_job(
            func=self.run_weekly_crawl,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),  # Ogni lunedì alle 9:00
            id='weekly_crawl',
            name='Weekly Bright Data Crawl',
            replace_existing=True
        )
        logger.info("Weekly crawl scheduled for every Monday at 9:00 AM")
    
    def run_weekly_crawl(self):
        """
        Esegui il crawl settimanale automatico
        """
        logger.info("Starting automated weekly crawl")
        
        db = SessionLocal()
        try:
            # Calcola il lunedì di questa settimana
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            
            # Controlla se il crawl settimanale è già stato avviato
            existing_schedule = db.query(WeeklyCrawlSchedule).filter(
                WeeklyCrawlSchedule.week_start == week_start,
                WeeklyCrawlSchedule.status.in_(["pending", "running"])
            ).first()
            
            if existing_schedule:
                logger.info(f"Weekly crawl already running for week {week_start}")
                return
            
            # Crea il record di schedulazione
            schedule = WeeklyCrawlSchedule(
                week_start=week_start,
                status="running",
                triggered_at=datetime.utcnow()
            )
            db.add(schedule)
            db.commit()
            
            # Ottieni tutte le mappature attive
            active_mappings = db.query(EsercenteSocialMapping).filter(
                EsercenteSocialMapping.is_active == "true"
            ).all()
            
            if not active_mappings:
                logger.warning("No active social mappings found")
                schedule.status = "completed"
                schedule.completed_at = datetime.utcnow()
                schedule.notes = "No active mappings found"
                db.commit()
                return
            
            logger.info(f"Found {len(active_mappings)} active mappings")
            
            # Raggruppa per platform
            platform_urls = {}
            for mapping in active_mappings:
                if mapping.platform not in platform_urls:
                    platform_urls[mapping.platform] = []
                
                url_data = {"url": mapping.url}
                if mapping.crawl_params:
                    url_data.update(mapping.crawl_params)
                
                platform_urls[mapping.platform].append(url_data)
            
            # Avvia i job per ogni platform
            triggered_jobs = []
            failed_jobs = []
            
            for platform, urls_data in platform_urls.items():
                urls = [item["url"] for item in urls_data]
                params = urls_data[0] if urls_data else {}
                params.pop("url", None)  # Rimuovi url dai params se presente
                
                try:
                    logger.info(f"Triggering crawl for {platform} with {len(urls)} URLs")
                    
                    response = brightdata_service.trigger_crawl(
                        platform=platform,
                        urls=urls,
                        params=params
                    )
                    
                    if response.get("success"):
                        # Salva il job nel database
                        job = brightdata_service.save_job_to_db(
                            db=db,
                            platform=platform,
                            urls=urls,
                            params=params,
                            response=response
                        )
                        
                        triggered_jobs.append({
                            "platform": platform,
                            "job_id": job.job_id,
                            "urls_count": len(urls)
                        })
                        logger.info(f"Successfully triggered {platform} crawl with job_id: {job.job_id}")
                    else:
                        failed_jobs.append({
                            "platform": platform,
                            "error": response.get("error", "Unknown error")
                        })
                        logger.error(f"Failed to trigger {platform} crawl: {response.get('error')}")
                
                except Exception as e:
                    logger.error(f"Exception triggering weekly crawl for {platform}: {e}")
                    failed_jobs.append({
                        "platform": platform,
                        "error": str(e)
                    })
            
            # Aggiorna il schedule
            schedule.total_jobs = len(triggered_jobs)
            schedule.failed_jobs = len(failed_jobs)
            
            if triggered_jobs:
                schedule.status = "running"
                logger.info(f"Weekly crawl initiated with {len(triggered_jobs)} jobs")
            else:
                schedule.status = "failed"
                schedule.completed_at = datetime.utcnow()
                schedule.notes = f"All jobs failed: {failed_jobs}"
                logger.error("All weekly crawl jobs failed")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error in weekly crawl scheduler: {e}")
        finally:
            db.close()
    
    def check_and_process_completed_jobs(self):
        """
        Controlla i job completati e li processa automaticamente
        """
        logger.info("Checking for completed jobs to process")
        
        db = SessionLocal()
        try:
            # Trova job completati non ancora processati
            completed_jobs = db.query(BrightDataJob).filter(
                BrightDataJob.status == "triggered",
                BrightDataJob.created_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            for job in completed_jobs:
                try:
                    # Controlla lo status del job
                    status_response = brightdata_service.get_job_status(job.job_id)
                    
                    if status_response.get("status") == "completed":
                        logger.info(f"Processing completed job: {job.job_id}")
                        
                        # Recupera e processa i risultati
                        results_response = brightdata_service.get_job_results(job.job_id)
                        
                        if results_response.get("success"):
                            results_data = results_response.get("data", [])
                            brightdata_service.save_results_to_db(db, job, results_data)
                            brightdata_service.integrate_with_esercenti(db, job)
                            
                            logger.info(f"Successfully processed {len(results_data)} results for job {job.job_id}")
                        else:
                            job.status = "failed"
                            job.error_message = results_response.get("error", "Failed to retrieve results")
                            db.commit()
                            logger.error(f"Failed to retrieve results for job {job.job_id}")
                    
                    elif status_response.get("status") == "failed":
                        job.status = "failed"
                        job.error_message = "Job failed on Bright Data"
                        job.completed_at = datetime.utcnow()
                        db.commit()
                        logger.error(f"Job {job.job_id} failed on Bright Data")
                
                except Exception as e:
                    logger.error(f"Error processing job {job.job_id}: {e}")
        
        finally:
            db.close()
    
    def schedule_job_checker(self):
        """
        Schedula il controllo dei job completati ogni ora
        """
        self.scheduler.add_job(
            func=self.check_and_process_completed_jobs,
            trigger=CronTrigger(minute=0),  # Ogni ora all'inizio dell'ora
            id='job_checker',
            name='Check Completed Jobs',
            replace_existing=True
        )
        logger.info("Job checker scheduled to run every hour")
    
    def start_all_schedules(self):
        """
        Avvia tutti gli scheduler
        """
        self.schedule_weekly_crawls()
        self.schedule_job_checker()
        logger.info("All schedulers started successfully")
    
    def stop(self):
        """
        Ferma tutti gli scheduler
        """
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

# Singleton instance
weekly_scheduler = WeeklyCrawlScheduler()