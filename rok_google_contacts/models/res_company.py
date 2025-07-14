from PIL import Image
from io import BytesIO
from datetime import datetime
import logging
import requests
import base64
from odoo import models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_import_google_contacts(self):
        """IMPORT Contacts FROM Google TO ODOO"""
        url = ("https://people.googleapis.com/v1/people/me/"
            "connections?personFields=names,addresses,"
            "emailAddresses,phoneNumbers,birthdays,coverPhotos,locales,locations,"
            "occupations,organizations,photos,relations,urls&pageSize=1000")
        headers = {
            'Authorization': f'Bearer {self.contact_company_access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get('connections', [])
            partners = []
            for connection in data:
                cnt_rsr_name = connection.get('resourceName', '')
                etag = connection.get('etag', '')
                names = connection.get('names', [{}])[0]
                first_name = names.get('givenName', '')
                last_name = names.get('familyName', '')
                name = names.get('displayName', '')
                emailAddresses = connection.get('emailAddresses', [{}])[0]
                email = emailAddresses.get('value', '')
                phoneNumbers = connection.get('phoneNumbers', [{}])[0]
                phone = phoneNumbers.get('value', '')

                street = ''
                street2 = ''
                city = ''
                pin = ''
                state_id = False
                country_id = False

                addresses = connection.get('addresses', [{}])[0]
                if addresses:
                    street = addresses.get('streetAddress', '')
                    street2 = addresses.get('extendedAddress', '')
                    city = addresses.get('city', '')
                    pin = addresses.get('postalCode', '')
                    state = addresses.get('region', '')
                    if state:
                        state = self.env['res.country.state'].search(
                            [("name", 'ilike', state)], limit=1)
                        state_id = state.id if state else False
                    country_code = addresses.get('countryCode', '')
                    if country_code:
                        country = self.env['res.country'].search(
                            [('code', 'ilike', country_code)], limit=1)
                        country_id = country.id if country else False
                birthday_info = connection.get('birthdays', [''])[0]
                birthday = ''
                if birthday_info:
                    birthday = birthday_info.get("text", "")
                    try:
                        birthday = datetime.strptime(birthday, '%m/%d/%Y').strftime('%Y-%m-%d')
                    except Exception as e:
                        _logger.warning("%s - %s: %s", name, cnt_rsr_name, e)
                        birthday = ""

                photos = connection.get('photos', '')
                image_1920 = False
                if photos:
                    photo_url = photos[0].get("url")
                    if photo_url:
                        try:
                            photo_resp = requests.get(photo_url)
                            if photo_resp.status_code == 200:
                                img = Image.open(BytesIO(photo_resp.content)).convert('RGB')
                                colors = img.getcolors(maxcolors=1000000)
                                if colors:
                                    # Colors is a list of (count, color)
                                    most_common = max(colors, key=lambda x: x[0])
                                    # If more than 90% of the pixels are the same color, it's a placeholder avatar
                                    if most_common[0] / (img.width * img.height) < 0.9:
                                        image_1920 = base64.b64encode(photo_resp.content)
                                    else:
                                        _logger.info("Skip avatar-like image for %s", name)
                                else:
                                    image_1920 = base64.b64encode(photo_resp.content)
                        except Exception as e:
                            _logger.warning("Failed to fetch photo for %s: %s", name, e)

                partner_vals = {
                    'name': name or '',
                    'first_name': first_name or '',
                    'last_name': last_name or '',
                    'email': email or '',
                    'street': street or '',
                    'street2': street2 or '',
                    'city': city or '',
                    'zip': pin or '',
                    'state_id': state_id or False,
                    'country_id': country_id or False,
                    'phone': phone,
                    'google_resource': cnt_rsr_name,
                    'google_etag': etag,
                    'birthday': birthday,
                    'image_1920': image_1920,
                }
                existing_partner = self.env['res.partner'].search(
                    [('google_resource', '=', cnt_rsr_name)], limit=1)
                if existing_partner:
                    existing_partner.write(partner_vals)
                    if partner_vals["birthday"]:
                        _logger.info("%s - %s", existing_partner.name, existing_partner.birthday)
                else:
                    partners.append(partner_vals)
            if partners:
                self.env['res.partner'].create(partners)
            _logger.info("Contact imported successfully!")
        else:
            error_message = f"Failed to import contact. Error: {response.text}"
            raise ValidationError(error_message)
