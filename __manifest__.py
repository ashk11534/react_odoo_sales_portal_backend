{
    'name': 'React Odoo Sales Portal',
    'version': '1.0',
    'summary': 'React Odoo Sales Portal App',
    'sequence': 200,
    'description': """Developed by Md. Ashikuzzaman.""",
    'category': '',
    'website': '',
    'depends': ['sale', 'product', 'project', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'assets': {},
    'license': 'LGPL-3',
}
