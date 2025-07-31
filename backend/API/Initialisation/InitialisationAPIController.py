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

def registerInitialisationRoutes(app, context):
    controller = InitialisationAPIController(context)

    @InitialisationBlueprint.route("/init/onboarding", methods=["GET"])
    def onboarding():
        g.PageTitle = "Onboarding"
        
        return controller.start_onboarding()
    
    @InitialisationBlueprint.route("/api/init/completeOnboarding", methods=["POST"])
    def completeOnboarding():
        try:
            features = request.get_json()
            
            for featureName, featureConfig in features.items():
                for key, value in featureConfig.items():
                    controlName = f"{featureName[0].upper()}{featureName[1:]}" if key == "enable" else key[0].upper() + key[1:]

                    if isinstance(value, bool):
                        value = int(value)

                    control = controller._context.session.query(SystemControls).filter(SystemControls.name == controlName).first()

                    if control:
                        control.value = str(value)
                    else:
                        control = SystemControls(name=controlName, value=str(value))
                        controller._context.session.add(control)

                    controller._context.session.commit()
                    
            isInitialised = controller._context.session.query(SystemControls).filter(SystemControls.name == "isInitialised").first()
            if not isInitialised:
                isInitialised = SystemControls(name="isInitialised", value="1")
                controller._context.session.add(isInitialised)
                
                controller._context.session.commit()
            else:
                isInitialised.value = "1"
                controller._context.session.commit()
            
            return jsonify({"message": "Onboarding completed successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @InitialisationBlueprint.route("/init/enableAndDisableFeatures", methods=["POST"])
    def enableAndDisableFeatures():        
        return controller.enableAndDisableFeatures(request.get_data())

    app.register_blueprint(InitialisationBlueprint)
