from torch.autograd import Variable


def subword_aware_accuracy_strict(subword_predictions: Variable, subword_targets: Variable,
                                  full_words_masks: Variable) -> float:
    compared = (subword_predictions == subword_targets)
    split = compared.expand_as(full_words_masks) * full_words_masks
    compared_with_mask = (split != full_words_masks)
    res = (compared_with_mask.sum(dim=1) == 0)
    n = res.size(0)
    return res.sum() / n


def subword_aware_accuracy(subword_predictions: Variable, subword_targets: Variable,
                           full_words_masks: Variable) -> float:
    compared = (subword_predictions == subword_targets)
    split = compared.expand_as(full_words_masks) * full_words_masks
    res = split.sum(1).float() / full_words_masks.sum(1).float()
    n = res.size(0)
    return res.sum() / n
