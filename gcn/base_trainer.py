import os
import sys
from sklearn.externals import joblib
from chariot.storage import Storage
import chariot.transformer as ct
from chariot.preprocessor import Preprocessor


class BaseTrainer():

    def __init__(self, root="", lang=None, min_df=5, max_df=sys.maxsize,
                 unknown="<unk>", preprocessor_name="preprocessor", log_dir=""):
        default_root = os.path.join(os.path.dirname(__file__), "../../")
        _root = root if root else default_root

        self.storage = Storage(_root)
        self.preprocessor_name = preprocessor_name
        self._base_log_dir = log_dir
        self._built = False
        self.preprocessor = Preprocessor(
                                text_transformers=[
                                    ct.text.UnicodeNormalizer(),
                                    ct.text.LowerNormalizer()
                                ],
                                tokenizer=ct.Tokenizer(lang=lang),
                                vocabulary=ct.Vocabulary(
                                            min_df=min_df, max_df=max_df,
                                            unknown=unknown))

    def load_preprocessor(self):
        if os.path.exists(self.preprocessor_path):
            self._built = True
            self.preprocessor = joblib.load(self.preprocessor_path)

    @property
    def preprocessor_path(self):
        if self._base_log_dir:
            path = self._log_dir + "/{}.pkl".format(self.preprocessor_name)
            return self.storage.data_path(path)
        else:
            path = "interim/{}.pkl".format(self.preprocessor_name)
            return self.storage.data_path(path)

    @property
    def _log_dir(self):
        folder = "/" + self._base_log_dir if self._base_log_dir else ""
        log_dir = "log{}".format(folder)
        if not os.path.exists(self.storage.data_path(log_dir)):
            os.mkdir(self.storage.data_path(log_dir))

        return log_dir

    @property
    def log_dir(self):
        return self.storage.data_path(self._log_dir)

    @property
    def model_path(self):
        return self.storage.data_path(self._log_dir + "/model.h5")

    @property
    def tensorboard_dir(self):
        return self.storage.data_path(self._log_dir)

    def download(self):
        raise Exception("You have to specify what kinds of data you use.")

    def build(self, data_kind="train", field="", save=True):
        if not self._built:
            self.load_preprocessor()
        if self._built:
            print("Load existing preprocessor {}.".format(
                os.path.basename(self.preprocessor_path)))
            return 0

        r = self.download()
        if data_kind == "test":
            data = r.test_data()
        elif data_kind == "valid":
            data = r.valid_data()
        else:
            data = r.train_data()

        print("Building Dictionary from {} data...".format(data_kind))
        if not field:
            self.preprocessor.fit(data)
        else:
            self.preprocessor.fit(data[field])

        if save:
            joblib.dump(self.preprocessor, self.preprocessor_path)
        self._built = True
        print("Done!")
