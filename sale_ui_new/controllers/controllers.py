# from odoo import http


# class SaleUiNew(http.Controller):
#     @http.route('/sale_ui_new/sale_ui_new', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_ui_new/sale_ui_new/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_ui_new.listing', {
#             'root': '/sale_ui_new/sale_ui_new',
#             'objects': http.request.env['sale_ui_new.sale_ui_new'].search([]),
#         })

#     @http.route('/sale_ui_new/sale_ui_new/objects/<model("sale_ui_new.sale_ui_new"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_ui_new.object', {
#             'object': obj
#         })

