def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized'}, 401
    
    @app.errorhandler(402)
    def payment_required(error):
        return {'error': 'Insufficient funds'}, 402
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        return {'error': 'Central Bank connectivity issues'}, 502
