import os
from app import create_app, db

app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()          # create tables if they don't exist
    app.run(host="0.0.0.0", port=5000, debug=(os.getenv("FLASK_ENV") == "development"))
