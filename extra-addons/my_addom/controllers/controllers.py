# from odoo import http


# class MyModyle(http.Controller):
#     @http.route('/my_modyle/my_modyle', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/my_modyle/my_modyle/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('my_modyle.listing', {
#             'root': '/my_modyle/my_modyle',
#             'objects': http.request.env['my_modyle.my_modyle'].search([]),
#         })

#     @http.route('/my_modyle/my_modyle/objects/<model("my_modyle.my_modyle"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('my_modyle.object', {
#             'object': obj
#         })

