from app import create_app
import sys
import io

app = create_app()

if __name__ == '__main__':
    # Fix Windows console encoding to UTF-8 to avoid codec errors with Vietnamese
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except Exception as _e:
            # Fallback silently; encoding issues will be shown in logs if any
            pass
    app.run(debug=True, host='0.0.0.0', port=5000)