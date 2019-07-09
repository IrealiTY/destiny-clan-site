import sys
from app import create_app

app = create_app()

if __name__ == "__main__":
    print(f'Args({len(sys.argv)}): {str(sys.argv)}')
    if len(sys.argv) > 1:
        if sys.argv[1] == '--debug':
            print('Debug enabled')
            app.run(debug=True, host='0.0.0.0')
    else:
        app.run()