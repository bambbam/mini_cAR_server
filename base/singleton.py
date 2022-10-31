class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = super(Singleton, class_).__new__(class_)
        return class_._instance
