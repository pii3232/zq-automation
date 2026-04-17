import sys
sys.path.insert(0, 'E:/5-ZDZS-TXA5/SERVER')

try:
    from app import create_app
    print("App created successfully")

    app = create_app()
    print("Flask app initialized")

    with app.app_context():
        from models import User
        count = User.query.count()
        print(f"Users in database: {count}")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
