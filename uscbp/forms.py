from django.forms.models import BaseInlineFormSet, inlineformset_factory, ModelForm

class BaseNestedFormset(BaseInlineFormSet):

    def add_fields(self, form, index):

        # allow the super class to create the fields as usual
        super(BaseNestedFormset, self).add_fields(form, index)

        form.nested = self.nested_formset_class(
            instance=form.instance,
            data=form.data if self.is_bound else None,
            prefix='%s-%s' % (
                form.prefix,
                self.nested_formset_class.get_default_prefix(),
                ),
        )

    def clean(self):
        super(BaseNestedFormset,self).clean()
        for form in self:
            form.nested.clean()

    def is_valid(self):

        result = super(BaseNestedFormset, self).is_valid()

        if self.is_bound:
            # look at any nested formsets, as well
            for form in self.forms:
                result = result and form.nested.is_valid()

        return result

    def save(self, commit=True):

        result = super(BaseNestedFormset, self).save(commit=commit)

        for form in self:
            form.nested.save(commit=commit)

        return result

def nested_formset_factory(parent_model, child_model, grandchild_model, form=ModelForm, nested_form=ModelForm,
                           fk_name=None, nested_fk_name=None, extra=0, nested_extra=0, max_num=None, nested_max_num=None,
                           can_delete=True, nested_can_delete=True):

    parent_child = inlineformset_factory(
        parent_model,
        child_model,
        formset=BaseNestedFormset,
        form=form,
        extra=extra,
        fk_name=fk_name,
        can_delete=can_delete,
        max_num=max_num
    )

    parent_child.nested_formset_class = inlineformset_factory(
        child_model,
        grandchild_model,
        form=nested_form,
        extra=nested_extra,
        fk_name=nested_fk_name,
        can_delete=nested_can_delete,
        max_num=nested_max_num
    )

    return parent_child