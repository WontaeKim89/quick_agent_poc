# 싱글톤 패턴
class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            # class_._instance = object().__new__(class_, *args, **kwargs)
            class_._instance = super(Singleton, class_).__new__(class_)
        return class_._instance


class SingletonInstane:
    __instance = None

    @classmethod
    def __getInstance(class_):
        return class_.__instance

    @classmethod
    def instance(class_, *args, **kargs):
        class_.__instance = class_(*args, **kargs)
        class_.instance = class_.__getInstance
        return class_.__instance
