import uvicorn
import asyncio
import app.api as main_api
import app.user.model as userModel
import app.payment.model as paymentModel
import app.googleSearchResult.model as googleSearchResult
import app.sentimentResult.model as sentimentResult
import app.userpayment.model as userpaymentModel
import app.intervention.model as interventionModel
import app.intervention_response.model as interventionresponseModel
import app.invoice.model as invoiceModel
import app.messaging.model as messageModel
import app.searchid_list.model as searchidlistModel
import app.promo_code.model as promocodeModel
import app.alert.model as alertModel
import app.cron_job.model as cronjobModel
import app.email_verify.model as emailverifyModel
from database import engine

userModel.Base.metadata.create_all(bind=engine)
userpaymentModel.Base.metadata.create_all(bind=engine)
paymentModel.Base.metadata.create_all(bind=engine)
googleSearchResult.Base.metadata.create_all(bind=engine)
sentimentResult.Base.metadata.create_all(bind=engine)
interventionModel.Base.metadata.create_all(bind=engine)
interventionresponseModel.Base.metadata.create_all(bind=engine)
invoiceModel.Base.metadata.create_all(bind=engine)
messageModel.Base.metadata.create_all(bind=engine)
searchidlistModel.Base.metadata.create_all(bind=engine)
promocodeModel.Base.metadata.create_all(bind=engine)
alertModel.Base.metadata.create_all(bind=engine)
cronjobModel.Base.metadata.create_all(bind=engine)
emailverifyModel.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # uvicorn.run("app.api:app", host="0.0.0.0", port=443, log_level="debug", ssl_certfile="certificate.crt", ssl_keyfile="private.key", workers=2, reload=False)
    uvicorn.run("app.api:app", host="0.0.0.0", port=80, log_level="debug", workers=2, reload=False)