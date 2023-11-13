import uvicorn
import ssl
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
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="privkey.pem")
    uvicorn.run("app.api:app", host="0.0.0.0", port=443, log_level="debug", ssl_version=ssl.PROTOCOL_TLS, ssl_context=ssl_context, workers=2, reload=False)
    # uvicorn.run("app.api:app", host="127.0.0.1", port=8000, log_level="debug", workers=2, reload=False)