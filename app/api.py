from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles

from app.alert.router import router as alert_router
from app.email_verify.router import router as email_verify_router
from app.googleSearchResult.router import router as googleSearchResult_router
from app.intervention.router import router as intervention_router
from app.invoice.router import router as invoice_router
from app.messaging.router import router as messaging_router
from app.payment.router import router as paymentlog_router
from app.promo_code.router import router as promo_code_router
from app.stripe_manager.router import router as stripe_manager_router
from app.user.router import router as user_router
from app.userpayment.router import router as userpayment_router
from app.websocket.ws import router as websocket_router

from app.cron_job.cron_job import CronJob
from app.websocket.ws import connected_clients

app = FastAPI(docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/build", StaticFiles(directory="build"), name='frontent')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    HTTPSRedirectMiddleware
)

app.include_router(alert_router)
app.include_router(email_verify_router)
app.include_router(googleSearchResult_router)
app.include_router(intervention_router)
app.include_router(invoice_router)
app.include_router(messaging_router)
app.include_router(paymentlog_router)
app.include_router(promo_code_router)
app.include_router(stripe_manager_router)
app.include_router(user_router)
app.include_router(userpayment_router)
app.include_router(websocket_router)

scheduler = AsyncIOScheduler()
scheduler.add_job(CronJob.weather_task, 'interval', minutes=15, args=[connected_clients])
scheduler.add_job(CronJob.serpapi_task, 'cron', day=1)
scheduler.start()

# route handlers
@app.exception_handler(404)
async def not_found_404(request, exc):
    return FileResponse("build/index.html")