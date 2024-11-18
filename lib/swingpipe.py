



class BasePipe:
    def process_frame(self, frame):
        raise NotImplementedError("Subclasses must implement this method")
    def process_perf_frame(self, perf_frame):
        raise NotImplementedError("Subclasses must implement this method")
    def preprocess_df(self, df):
        raise NotImplementedError("Subclasses must implement this method")