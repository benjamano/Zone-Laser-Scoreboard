from flask import jsonify, render_template, Blueprint, g, request
from data.models import SystemControls

InitialisationBlueprint = Blueprint("Initialisation", __name__)

class InitialisationAPIController:
    def __init__(self, context):
        self._context = context

    def start_onboarding(self):
        isInitialised = self._context.session.query(SystemControls).filter(SystemControls.name == "isInitialised").first()
        
        if isInitialised and isInitialised.value == 1:
            return jsonify({"message": "System already initialised"}), 400
        
        return render_template("Onboarding/onboarding.html"), 200
    
    def enableAndDisableFeatures(self, data : list):
        for key, value in data.enumerate():
            pass
        return

def registerInitialisationRoutes(app, context):
    controller = InitialisationAPIController(context)

    @InitialisationBlueprint.route("/init/onboarding", methods=["GET"])
    def onboarding():
        g.PageTitle = "Onboarding"
        
        return controller.start_onboarding()
    
    @InitialisationBlueprint.route("/init/enableAndDisableFeatures", methods=["POST"])
    def enableAndDisableFeatures():        
        return controller.enableAndDisableFeatures(request.get_data())

    app.register_blueprint(InitialisationBlueprint)
