from tree import Tree
import numpy as np

class EpochEvaluator:
    def __init__(self):
        pass
    
    def evaluate_epoch_avg(self, scores):
        res = 0
        for s in scores:
            res += s
        res = res / len(scores)
        return res
    
    def evaluate_epoch_min(self, scores):
        res = min(scores)
        return res
    
    def evaluate_epoch_median(self, scores):
        i = len(scores)//2
        res = sorted(scores)[i]
        if len(scores) % 2 == 0:
            res = (res + sorted(scores)[i-1])/2.0
        return res
    
    def evaluate_epoch_inlier(self, scores, f):
        sorted_scores = sorted(scores)
        q1 = sorted_scores[len(scores)//4]
        q3 = sorted_scores[int(3*len(scores)/4)]
        iqr = q3-q1
        w_inf = q1-1.5*iqr
        w_sup = q3+1.5*iqr

        inliers = []
        for s in sorted_scores:
            if s < w_inf:
                continue
            if s > w_sup:
                break
            inliers.append(s)

        return f(inliers)
    
    def evaluate_epoch_inlier_and_bad_outlier(self, scores, f):
        sorted_scores = sorted(scores)
        q1 = sorted_scores[len(scores)//4]
        q3 = sorted_scores[int(3*len(scores)/4)]
        iqr = q3-q1
        w_sup = q3+1.5*iqr

        inliers_and_bad_outliers = []
        for s in sorted_scores:
            if s > w_sup:
                break
            inliers_and_bad_outliers.append(s)

        return f(inliers_and_bad_outliers)
    
    def evaluate_epoch_avg_minus_sd(self, scores):
        avg = self.evaluate_epoch_avg(scores)
        var = np.var(scores)
        sd = var ** 0.5

        return avg - sd

