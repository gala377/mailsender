from flask.views import MethodView


class ViewBase(MethodView):
    name = None
    route = None

    __subclasses = []

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if cls.name is None:
            raise ValueError("Views `name` has o be set")
        if cls.route is None:
            raise ValueError("Views `route` has to be set")
        cls.__subclasses.append(cls)

    @classmethod
    def init_app(cls, app):
        for view in cls.__subclasses:
            app.add_url_rule(
                view.route,
                view_func=view.as_view(view.name))


class HelloView(ViewBase):
    name = "hello"
    route = "/hello"

    def get(self):
        return "Hello World!"

