import os
import unittest
from app import create_app
from models import db, Admin, Business

class HiddenAdminTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.business = Business.query.first()
        self.site_admin = Admin.query.filter_by(username='siteadmin').first()
        self.bus_admin = Admin.query.filter_by(username='busadmin').first()
        self.hidden_admin = Admin.query.filter_by(username='hiddenadmin').first()
        
    def tearDown(self):
        self.app_context.pop()
        
    def login(self, username, password):
        return self.client.post('/dashboard/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
        
    def login_site_admin(self, username, password):
        return self.client.post('/site-admin/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
        
    def test_business_admin_visibility(self):
        self.login('busadmin', 'password')
        response = self.client.get(f'/business/{self.business.business_slug}/users/manage')
        html = response.get_data(as_text=True)
        # Should contain busadmin
        self.assertIn('busadmin', html)
        # Should NOT contain hiddenadmin
        self.assertNotIn('hiddenadmin', html)
        
    def test_site_admin_visibility(self):
        self.login_site_admin('siteadmin', 'password')
        response = self.client.get(f'/site-admin/users/{self.business.id}')
        html = response.get_data(as_text=True)
        # Should contain both
        self.assertIn('busadmin', html)
        self.assertIn('hiddenadmin', html)
        # Should contain the Hidden badge
        self.assertIn('Hidden', html)
        
    def test_permission_bypass(self):
        self.login('busadmin', 'password')
        # Try to edit hidden admin
        response = self.client.get(f'/business/{self.business.business_slug}/users/edit/{self.hidden_admin.id}')
        self.assertEqual(response.status_code, 403)
        
        # Try to delete hidden admin
        response = self.client.post(f'/business/{self.business.business_slug}/users/delete/{self.hidden_admin.id}')
        self.assertEqual(response.status_code, 403)
        
        # Try to edit visible admin (should work)
        response = self.client.get(f'/business/{self.business.business_slug}/users/edit/{self.bus_admin.id}')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
