import json, base64

from odoo import http
from odoo.http import request as req


class LoginPortalUser(http.Controller):
    @http.route('/login-react-sales-portal-user', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False,
                cors='*')
    def login_portal_user(self, **kwargs):
        form_data = req.httprequest.form

        email = form_data.get('email').strip() if form_data.get('email') else ''
        password = form_data.get('password') if form_data.get('password') else ''

        db_name = req.env.cr.dbname

        try:
            user_id = req.env['res.users'].sudo().authenticate(
                db_name, email, password, user_agent_env={'base_location': req.httprequest.host_url}
            )

            if user_id:
                user = req.env['res.users'].sudo().browse(user_id)

                admin_user_id = req.env['res.users'].sudo().authenticate(
                    db_name, 'admin', 'odoo17', user_agent_env={'base_location': req.httprequest.host_url}
                )

                if admin_user_id:
                    req.session.uid = admin_user_id
                    response = req.make_response(
                        json.dumps({'code': 200, 'user_id': user.id}),
                        headers=[
                            ('Content-Type', 'application/json'),
                            ('Access-Control-Allow-Methods', 'POST, OPTIONS')
                        ]
                    )
                    return response
                else:
                    raise Exception("Admin authentication failed")

        except Exception as e:
            response = req.make_response(
                json.dumps({'code': 404, 'error': str(e)}),
                headers=[
                    ('Content-Type', 'application/json'),
                    ('Access-Control-Allow-Methods', 'POST, OPTIONS')
                ]
            )
            return response


class SearchUser(http.Controller):
    @http.route('/search-user', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def search_user(self, **kwargs):
        form_data = req.httprequest.form
        user_id = int(form_data.get('userId')) if form_data.get('userId') else None
        user = req.env['res.users'].sudo().browse(user_id)

        user_image = ''

        if user.image_1920:
            image_base64 = base64.b64decode(user.image_1920)
            user_image = base64.b64encode(image_base64).decode('utf-8')

        return req.make_response(json.dumps({'code': 200, 'user_image': user_image}), headers=[
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS')
        ])


class RetrieveQuotations(http.Controller):
    @http.route('/retrieve-quotations', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def retrieve_quotations(self, **kwargs):
        form_data = req.httprequest.form
        user_id = int(form_data.get('userId')) if form_data.get('userId') else None
        user = req.env['res.users'].sudo().browse(user_id)

        quotations = req.env['sale.order'].sudo().search([('react_portal_sales_person', '=', user.id)])

        data = []

        for quotation in quotations:
            data.append({
                'quotation_id': quotation.id,
                'quotation_state': quotation.state,
                'quotation_name': quotation.name,
                'order_date': quotation.format_order_date(),
                'customer_name': quotation.partner_id.name,
                'amount_total': quotation.amount_total,
            })

        return req.make_response(json.dumps({'code': 200, 'quotation_data': data}), headers=[
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS')
        ])


class SearchCustomer(http.Controller):
    @http.route('/search-customer', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def search_customer(self, **kwargs):
        form_data = req.httprequest.form
        customer_name = form_data.get('customerName').strip() if form_data.get('customerName') else None
        customers = req.env['res.partner'].sudo().search([('name', 'ilike', customer_name)])

        data = []

        for customer in customers:
            data.append({
                'customer_id': customer.id,
                'customer_name': customer.name
            })

        return req.make_response(json.dumps({'code': 200, 'customer_data': data}), headers=[
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS')
        ])


class SearchProduct(http.Controller):
    @http.route('/search-product', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def search_product(self, **kwargs):
        form_data = req.httprequest.form
        product_name = form_data.get('productName').strip() if form_data.get('productName') else None
        products = req.env['product.template'].sudo().search([('name', 'ilike', product_name), ('detailed_type', '=', 'product')])

        data = []

        for product in products:
            data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_price': product.list_price
            })

        return req.make_response(json.dumps({'code': 200, 'product_data': data}), headers=[
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS')
        ])


class CreateQuotation(http.Controller):
    @http.route('/create-quotation', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def create_quotation(self, **kwargs):
        print(req.session.uid)
        form_data = req.httprequest.form
        sales_person_id = int(form_data.get('salesPersonId')) if form_data.get('salesPersonId') else None
        customer_id = int(form_data.get('selectedCustomerId')) if form_data.get('selectedCustomerId') else None
        expiration_date = form_data.get('expirationDate')
        quotation_date = form_data.get('quotationDate')
        products = json.loads(form_data.get('selectedProducts')) if form_data.get('selectedProducts') else []

        print(products)

        # Creating a new quotation (start)

        new_quotation = req.env['sale.order'].sudo().create({
            'partner_id': customer_id,
            'react_portal_sales_person': sales_person_id,
            'validity_date': expiration_date,
            'date_order': quotation_date,
            'company_id': 1
        })

        # print(new_quotation)
        for product in products:
            uom = req.env['product.product'].sudo().search([('product_tmpl_id', '=', int(product.get('product_id')))]).uom_id
            product_obj = req.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', int(product.get('product_id')))], limit=1)

            req.env['sale.order.line'].sudo().create({
                'product_id': product_obj.id,
                'name': product_obj.name,
                'product_uom_qty': int(product.get('product_qty')),
                'product_uom': uom.id,
                'price_unit': float(product.get('product_price')),
                'order_id': new_quotation.id,
                'customer_lead': 1,
                'tax_id': False,
                'company_id': 1,
                'price_reduce_taxexcl': 0.0,
                'price_reduce_taxinc': 0.0,
                'price_subtotal': 0.0,
                'price_tax': 0.0,
                'price_total': 0.0
            })

            new_quotation.sudo().action_confirm()

        # Creating a new quotation (end)

        return req.make_response(json.dumps({'code': 200}), headers=[
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS')
        ])

    @http.route('/test-session-2', type='http', auth='public', csrf=False)
    def test_session(self, **kw):
        print('hmmm', req.env.user.name)

        session = req.session.context

        return req.render('ultima.test_session_template', {
            'session': req.session.context
        })
