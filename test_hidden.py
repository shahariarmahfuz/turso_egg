import unittest
from app import create_app
from models import Admin, Business

class TestHidden(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        with self.app.app_context():
            self.business = Business.query.first()
            self.hidden_admin = Admin.query.filter_by(username='hiddenadmin').first()
            self.bus_admin = Admin.query.filter_by(username='busadmin').first()

    def test_business_admin_visibility(self):
        with self.client as c:
            c.post('/dashboard/login', data=dict(username='busadmin', password='password'))
            res = c.get(f'/business/{self.business.business_slug}/users/manage')
            html = res.get_data(as_text=True)
            self.assertIn('busadmin', html)
            self.assertNotIn('hiddenadmin', html)

    def test_site_admin_visibility(self):
        with self.client as c:
            c.post('/site-admin/login', data=dict(username='siteadmin', password='password'))
            res = c.get(f'/site-admin/users/{self.business.id}')
            html = res.get_data(as_text=True)
            self.assertIn('busadmin', html)
            self.assertIn('hiddenadmin', html)
            self.assertIn('Hidden', html)

    def test_permission_bypass(self):
        with self.client as c:
            c.post('/dashboard/login', data=dict(username='busadmin', password='password'))
            # Try to edit hidden admin
            res1 = c.get(f'/business/{self.business.business_slug}/users/edit/{self.hidden_admin.id}')
            self.assertEqual(res1.status_code, 403)
            # Try to delete hidden admin
            res2 = c.post(f'/business/{self.business.business_slug}/users/delete/{self.hidden_admin.id}')
            self.assertEqual(res2.status_code, 403)
            
            # Edit visible admin
            res3 = c.get(f'/business/{self.business.business_slug}/users/edit/{self.bus_admin.id}')
            self.assertEqual(res3.status_code, 200)

if __name__ == '__main__':
    unittest.main()
