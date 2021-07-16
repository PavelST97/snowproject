from django.contrib import admin
from django.forms import ModelForm
from .models import *
from django.utils.safestring import mark_safe


class ProductAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            """<span style="color:red; font-size=14px;">При загрузке изображения с разрешением больше  {}x{} оно будет обрезано!</span>
            """.format(
                *Product.MAX_RESOLUTION
            )
        )
        self.fields['discount_price'].widget.attrs.update({
            'readonly': True, 'style': 'background: lightgray'
        })

    def clean(self):
        if not self.cleaned_data['discount']:
            self.cleaned_data['discount_price'] = None
        return self.cleaned_data


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    change_form_template = 'main/admin.html'


admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
