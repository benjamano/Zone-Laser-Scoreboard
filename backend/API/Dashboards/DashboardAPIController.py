from flask import Blueprint, jsonify, request
from data.models import *

DashboardBlueprint = Blueprint("Dashboards", __name__)

class DashboardAPIController:
    def __init__(self, context):
        self._context : SQLAlchemy = context

    def getDashboards(self):
        dashboards = self._context.session.query(DashboardCategory).filter_by(isActive=True).all()
        return jsonify([d.to_dict() for d in dashboards]), 200

    def getDashboard(self, dashboard_id):
        dashboard = self._context.session.query(DashboardCategory).filter_by(id=dashboard_id).first()
        if not dashboard:
            return jsonify({"error": "Dashboard not found"}), 404
        return jsonify(dashboard.to_dict()), 200

    def deleteDashboard(self, dashboard_id):
        dashboard = self._context.session.query(DashboardCategory).filter_by(id=dashboard_id).first()
        if not dashboard:
            return jsonify({"error": "Dashboard not found"}), 404

        self._context.session.delete(dashboard)
        self._context.session.commit()
        return jsonify({"message": "Dashboard deleted"}), 200

    def addDashboard(self):
        data = request.json
        if not data:
            return jsonify({"error": "Missing dashboard data"}), 400

        new_dashboard = DashboardCategory(
            name=data.get("name"),
            isActive=True,
        )
        self._context.session.add(new_dashboard)
        self._context.session.commit()
        return jsonify(new_dashboard.to_dict()), 201

    def updateDashboard(self, dashboardId):
        dashboard : DashboardCategory = self._context.session.query(DashboardCategory).filter_by(id=dashboardId).first()
        if not dashboard:
            return jsonify({"error": "Dashboard not found"}), 404

        data = request.json
        
        if "name" in data:
            dashboard.name = data.get("name", dashboard.name)
        if "isActive" in data:
            dashboard.isActive = data.get("isActive", dashboard.isActive)
        if "widgets" in data:
            dashboardWidgets = self._context.session.query(DashboardWidget).filter_by(categoryId=dashboard.id).all()
            
            for widget in data["widgets"]:
                widgetId = widget.get("id")
                existingWidget = next((w for w in dashboardWidgets if w.id == int(widgetId)), None)

                if existingWidget:
                    existingWidget.height = widget.get("height", existingWidget.height)
                    existingWidget.width = widget.get("width", existingWidget.width)
                    existingWidget.left = widget.get("left", existingWidget.left)
                    existingWidget.top = widget.get("top", existingWidget.top)
                    existingWidget.typeId = widget.get("type", existingWidget.typeId)
                    existingWidget.content = widget.get("content", existingWidget.content)
                    existingWidget.isActive = widget.get("isActive", existingWidget.isActive)
                else:
                    newWidget = DashboardWidget(
                        categoryId = dashboard.id,
                        height = widget.get("height", 1),
                        width = widget.get("width", 1),
                        left = widget.get("left", 0),
                        top = widget.get("top", 0),
                        typeId = widget.get("type"),
                        content = widget.get("content", None),
                        isActive = widget.get("isActive", True),
                    )
                    self._context.session.add(newWidget)

        self._context.session.commit()
        return jsonify((self._context.session.query(DashboardCategory).filter_by(id=dashboardId).first()).to_dict()), 200

    def deleteDashboardWidget(self, widgetId):
        widget : DashboardWidget = self._context.session.query(DashboardWidget).filter_by(id=widgetId).first()
        if not widget:
            return jsonify({"error": "Widget not found"}), 404

        widget.isActive = False
        
        self._context.session.commit()
        
        return jsonify({"message": "Widget deleted"}), 200

def registerDashboardRoutes(app, context):
    controller = DashboardAPIController(context)

    @DashboardBlueprint.route("/api/dashboards", methods=["GET"])
    def getDashboards():
        return controller.getDashboards()

    @DashboardBlueprint.route("/api/dashboards/<dashboardId>", methods=["GET"])
    def getDashboard(dashboardId):
        return controller.getDashboard(dashboardId)

    @DashboardBlueprint.route("/api/dashboards/<dashboardId>", methods=["DELETE"])
    def deleteDashboard(dashboardId):
        return controller.deleteDashboard(dashboardId)

    @DashboardBlueprint.route("/api/dashboards", methods=["POST"])
    def addDashboard():
        return controller.addDashboard()

    @DashboardBlueprint.route("/api/dashboards/<dashboardId>", methods=["PUT"])
    def updateDashboard(dashboardId):
        return controller.updateDashboard(dashboardId)
    
    @DashboardBlueprint.route("/api/dashboards/widgets/<widgetId>", methods=["DELETE"])
    def deleteDashboardWidget(widgetId):
        return controller.deleteDashboardWidget(widgetId)

    app.register_blueprint(DashboardBlueprint)
