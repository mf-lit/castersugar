from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    from app import routes
    app.register_blueprint(routes.bp)

    # Initialize and start the metadata health check service
    from app.metadata_health_check import MetadataHealthCheckService
    from app.chromecast_service import chromecast_service
    from app.dynamodb_service import dynamodb_service
    from app.icy_metadata_service import icy_metadata_service
    from app.bbc_metadata_service import bbc_metadata_service
    import app.metadata_health_check as health_check_module

    health_check_module.metadata_health_check_service = MetadataHealthCheckService(
        chromecast_service=chromecast_service,
        dynamodb_service=dynamodb_service,
        icy_metadata_service=icy_metadata_service,
        bbc_metadata_service=bbc_metadata_service
    )
    health_check_module.metadata_health_check_service.start()

    return app
