from app import app, db, User

def create_admin():
    with app.app_context():
        existing_admin = User.query.filter_by(email='admin@example.com').first()
        if existing_admin:
            print("Admin user already exists.")
            return
        
        admin = User(name='Admin Name', email='admin@example.com', admin=True)
        admin.set_password('yourStrongPassword')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")

if __name__ == '__main__':
    create_admin()
