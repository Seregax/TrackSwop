from dynamic_form import DynamicForm
from view_model import ViewModel
from service_spec import service_spec


view_model = ViewModel()

form = DynamicForm(service_spec, view_model)

form.render()

print(view_model.get_all())