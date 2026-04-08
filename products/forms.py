from django import forms
from .models import Product, Category


class SellerProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "price",
            "original_price",
            "stock",
            "is_active",
            "image",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter product name"
            }),
            "category": forms.Select(attrs={
                "class": "form-control"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter product description",
                "rows": 5
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter selling price"
            }),
            "original_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter original price"
            }),
            "stock": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter stock quantity",
                "min": "0"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.all().order_by("name")

        self.fields["name"].label = "Product Name"
        self.fields["category"].label = "Category / Subcategory"
        self.fields["description"].label = "Description"
        self.fields["price"].label = "Selling Price"
        self.fields["original_price"].label = "Original Price"
        self.fields["stock"].label = "Stock"
        self.fields["is_active"].label = "Active Product"
        self.fields["image"].label = "Main Product Image"

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        original_price = cleaned_data.get("original_price")

        if price is not None and price < 0:
            self.add_error("price", "Price cannot be negative.")

        if original_price is not None and original_price < 0:
            self.add_error("original_price", "Original price cannot be negative.")

        if price and original_price and original_price < price:
            self.add_error("original_price", "Original price should be greater than or equal to selling price.")

        return cleaned_data