from Data.models import InternalServerError
import datetime
import threading
from Utilities.format import Format

f = Format("ISE Logger")

def logInternalServerError(app, context, ise: InternalServerError) -> None:
    def _log():
        try:
            if context is not None and ise is not None:
                if ise.severity == 1:
                    f.message(f"SEVERE EXCEPTION: Logging severe error from {ise.service}. \tException Message: {ise.exception_message}", type="error")
                else:
                    f.message(f"EXCEPTION: Logging error from {str(ise.service).upper()}: {ise.exception_message}", type="warning")

                ise.timestamp = datetime.datetime.now()

                with app.app_context():
                    context.db.session.add(ise)
                    context.db.session.commit()
        except Exception as e:
            f.message(f"Error occurred while logging internal server error: {e}", type="error")

    threading.Thread(target=_log, daemon=True).start()