class Face:
    def __init__(self, image,prediction,final=None,id=None):
        self.image = image
        self.prediction = prediction
        if final == None:
            self.final = prediction
        else:
            self.final = final
        self.id = id