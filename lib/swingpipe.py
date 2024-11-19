import time

"""

# Example usage
if __name__ == "__main__":
    pipe = MyPipe()

    # Measure execution times
    pipe.measure_time(pipe.process_frame, frame="frame_data")
    pipe.measure_time(pipe.process_perf_frame, perf_frame="perf_frame_data")
    pipe.measure_time(pipe.preprocess_df, df="df_data")

    # Print execution summary
    print(pipe.get_execution_summary())

"""

class BasePipe:
    def __init__(self):
        # Define the base configuration dictionary with default values
        self.config = {
            "enable": True,
            "name": "undef",
            "render_on_dtl": False,
            "render_on_face": False,
            "render_static": False,
            "render_tracking": False,
            "render_trace": False
        }
        # Dictionary to store execution times of methods
        self.execution_times = {}
        
    def process_static_frame(self, frame,df,idx):
        raise NotImplementedError("Subclasses must implement this method")

    def process_tracking_frame(self, frame,df,idx):
        raise NotImplementedError("Subclasses must implement this method")
    
    def process_trace_frame(self,frame,df,idx):
        raise NotImplementedError("Subclasses must implement this method")

    def preprocess_df(self, df):
        raise NotImplementedError("Subclasses must implement this method")
        
    def update_config(self, **kwargs):
        """
        Update the configuration dictionary with new values.
        
        :param kwargs: Key-value pairs of configuration options to update or add.
        """
        self.config.update(kwargs)

    def measure_time(self, func, *args, **kwargs):
        """
        Measure the execution time of a function and store it in the execution_times dictionary.
        
        :param func: The function to execute.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        :return: The result of the function call.
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        method_name = func.__name__
        if method_name in self.execution_times:
            self.execution_times[method_name].append(end_time - start_time)
        else:
            self.execution_times[method_name] = [end_time - start_time]
        return result

    def get_execution_summary(self):
        """
        Get a summary of the execution times for all methods.
        
        :return: A dictionary with method names as keys and their total and average execution time as values.
        """
        summary = {}
        for method_name, times in self.execution_times.items():
            total_time = sum(times)
            avg_time = total_time / len(times) if times else 0
            summary[method_name] = {
                "total_time": total_time,
                "avg_time": avg_time,
                "count": len(times)
            }
        return summary