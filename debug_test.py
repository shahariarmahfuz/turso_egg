from app import create_app
from models import Admin
app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

response = client.post('/site-admin/login', data=dict(
    username='siteadmin',
    password='password'
), follow_redirects=True)

html = response.get_data(as_text=True)
print("Login successful:", 'site_admin_dashboard' in html or 'Businesses' in html)
if 'Redirecting...' in html:
    print("Redirecting issue!")
print("Response code:", response.status_code)
