from typing import List
import numpy as np
from util import make_directories_as_necessary
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
sns.set()
from random import random
from tqdm import tqdm
from sklearn.metrics import f1_score
import warnings


def make_csv_used_to_compute_mcnemar_bowker(predicted_labels_1, model_name_1, predicted_labels_2, model_name_2,
                                            filename):
    highest_val_to_go_up_to = max(max(predicted_labels_1), max(predicted_labels_2))
    total_num_categories = highest_val_to_go_up_to + 1
    model1label_to_allcorrmodel2labels = {}
    for i in range(highest_val_to_go_up_to + 1):
        model1label_to_allcorrmodel2labels[i] = []
    assert len(predicted_labels_2) == len(predicted_labels_1)
    for i in range(len(predicted_labels_2)):
        label_1 = predicted_labels_1[i]
        label_2 = predicted_labels_2[i]
        model1label_to_allcorrmodel2labels[label_1].append(label_2)
    model1label_to_model2label_to_count = {}
    for i in range(total_num_categories):
        model1label_to_model2label_to_count[i] = {}
        for j in range(total_num_categories):
            model1label_to_model2label_to_count[i][j] = model1label_to_allcorrmodel2labels[i].count(j)
    empty_cells_before_name = 2 + (total_num_categories // 2)
    num_fields_per_line = total_num_categories + 2
    str_to_write = ','.join(([''] * empty_cells_before_name) + [model_name_2] +
                            ([''] * (num_fields_per_line - empty_cells_before_name - 1))) + '\n'
    str_to_write += ','.join(['', ''] + [str(i) for i in range(total_num_categories)]) + '\n'
    for i in range(total_num_categories):
        if i + 2 == empty_cells_before_name:
            initial_field = model_name_1
        else:
            initial_field = ''
        line_fields = [initial_field, str(i)]
        for j in range(total_num_categories):
            line_fields.append(str(model1label_to_model2label_to_count[i][j]))
        str_to_write += ','.join(line_fields) + '\n'

    make_directories_as_necessary(filename)
    with open(filename, 'w') as f:
        f.write(str_to_write)


def plot_two_precision_recalls_against_each_other(recall_precision_points_one, label_one, recall_precision_points_two,
                                                  label_two, plot_filename, plot_title=None):
    make_directories_as_necessary(plot_filename)
    fig = plt.figure()

    recalls_one = []
    precisions_one = []
    for i in range(len(recall_precision_points_one)):
        recalls_one.append(recall_precision_points_one[i][0])
        precisions_one.append(recall_precision_points_one[i][1])
    plt.ylim(0, 1.05)
    plt.xlim(0, 1.05)

    plt.plot(recalls_one, precisions_one, label=label_one, color='blue')

    recalls_two = []
    precisions_two = []
    for i in range(len(recall_precision_points_two)):
        recalls_two.append(recall_precision_points_two[i][0])
        precisions_two.append(recall_precision_points_two[i][1])

    plt.plot(recalls_two, precisions_two, label=label_two, color='orange')

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    if plot_title is not None:
        plt.title(plot_title)
    plt.legend()

    plt.savefig(plot_filename, bbox_inches='tight')
    plt.close(fig)

    just_first_part_filename = plot_filename[:plot_filename.rfind('.')] + '-' + label_one.replace(' ', '_') + \
                               plot_filename[plot_filename.rfind('.'):]
    fig = plt.figure()
    plt.plot(recalls_one, precisions_one, label=label_one, color='blue')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    if plot_title is not None:
        plt.title(plot_title)
    plt.savefig(just_first_part_filename, bbox_inches='tight')
    plt.close(fig)

    just_second_part_filename = plot_filename[:plot_filename.rfind('.')] + '-' + label_two.replace(' ', '_') + \
                                plot_filename[plot_filename.rfind('.'):]
    fig = plt.figure()
    plt.plot(recalls_two, precisions_two, label=label_two, color='orange')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    if plot_title is not None:
        plt.title(plot_title)
    plt.savefig(just_second_part_filename, bbox_inches='tight')
    plt.close(fig)


def get_recall_precision_curve_points(list_of_logits, actual_labels_as_list_of_ints: List[int], string_prefix=''):
    assert list_of_logits[0].shape[-1] == 2
    assert actual_labels_as_list_of_ints.count(0) + actual_labels_as_list_of_ints.count(1) == \
           len(actual_labels_as_list_of_ints)
    list_of_probs = []
    for i, logit_pair in enumerate(list_of_logits):
        denom = np.log(np.sum(np.exp(logit_pair)))
        list_of_probs.append((np.exp(logit_pair - denom), actual_labels_as_list_of_ints[i]))
    if len(list_of_logits[0].shape) == 2:
        sorted_by_prob = sorted(list_of_probs, key=lambda x: x[0][0][1], reverse=True)
    else:
        sorted_by_prob = sorted(list_of_probs, key=lambda x: x[0][1], reverse=True)

    total_actual_positive_instances = actual_labels_as_list_of_ints.count(1)
    # precision = true_guessed_pos / true_guessed_pos + false_guessed_pos
    # recall = true_guessed_pos / total_actual_positive_instances
    recall_precision_points_to_return = []

    true_guessed_positive_so_far = 0
    best_sum_thresholds_so_far = []
    best_sum_threshold_recprecs = []
    best_sum_of_precrec = 0
    best_euclidean_thresholds_so_far = []
    best_euclidean_threshold_recprecs = []
    best_squared_euclidean_distance = 2
    for total_guessed_positive_so_far_minus_1 in range(len(sorted_by_prob)):
        true_guessed_positive_so_far += sorted_by_prob[total_guessed_positive_so_far_minus_1][-1]  # the true label
        precision_here = true_guessed_positive_so_far / (total_guessed_positive_so_far_minus_1 + 1)
        recall_here = true_guessed_positive_so_far / total_actual_positive_instances
        recall_precision_points_to_return.append((recall_here, precision_here))
        if recall_here + precision_here > best_sum_of_precrec:
            best_sum_of_precrec = recall_here + precision_here
            best_sum_thresholds_so_far = [sorted_by_prob[total_guessed_positive_so_far_minus_1][0][1]]
            best_sum_threshold_recprecs = [(recall_here, precision_here)]
        elif recall_here + precision_here == best_sum_of_precrec:
            best_sum_thresholds_so_far.append(sorted_by_prob[total_guessed_positive_so_far_minus_1][0][1])
            best_sum_threshold_recprecs.append((recall_here, precision_here))
        cur_euclidean_distance_squared = (recall_here * recall_here) - (2 * recall_here) + \
                                         (precision_here * precision_here) - (2 * precision_here) + 2
        if cur_euclidean_distance_squared < best_squared_euclidean_distance:
            best_squared_euclidean_distance = cur_euclidean_distance_squared
            best_euclidean_thresholds_so_far = [sorted_by_prob[total_guessed_positive_so_far_minus_1][0][1]]
            best_euclidean_threshold_recprecs = [(recall_here, precision_here)]
        elif cur_euclidean_distance_squared == best_squared_euclidean_distance:
            best_euclidean_thresholds_so_far.append(sorted_by_prob[total_guessed_positive_so_far_minus_1][0][1])
            best_euclidean_threshold_recprecs.append((recall_here, precision_here))
    print(string_prefix + 'Best thresholds for deciding something is positive:')
    if len(best_sum_thresholds_so_far) > 1:
        print('\tUsing sum of precision and recall, positive probability >= ' +
              'any threshold in range [' + str(best_sum_thresholds_so_far[-1]) + ', ' +
              str(best_sum_thresholds_so_far[0]) + '] (corresponding to (recall, precision) points ' +
              str(best_sum_threshold_recprecs) + ')')
    else:
        print('\tUsing sum of precision and recall, positive probability >= ' +
              str(best_sum_thresholds_so_far[0]) + ' (corresponding to recall ' +
              str(best_sum_threshold_recprecs[0][0]) + ' and precision ' + str(best_sum_threshold_recprecs[0][1]) + ')')
    if len(best_euclidean_thresholds_so_far) > 1:
        print('\tUsing Euclidean distance from point (1, 1), positive probability >= ' +
              'any threshold in range [' + str(best_euclidean_thresholds_so_far[-1]) + ', ' +
              str(best_euclidean_thresholds_so_far[0]) + '] (corresponding to (recall, precision) points ' +
              str(best_euclidean_threshold_recprecs) + ')')
    else:
        print('\tUsing Euclidean distance from point (1, 1), positive probability >= ' +
              str(best_euclidean_thresholds_so_far[0]) + ' (corresponding to recall ' +
              str(best_euclidean_threshold_recprecs[0][0]) + ' and precision ' +
              str(best_euclidean_threshold_recprecs[0][1]) + ')')
    return recall_precision_points_to_return


def bootstrap_f1(list_of_predicted_labels_roberta, list_of_predicted_labels_baseline, list_of_correct_labels,
                 num_times_to_bootstrap, filename_to_write_data_to, num_labels):
    tups_to_draw_from = \
        list(zip(list_of_predicted_labels_roberta, list_of_predicted_labels_baseline, list_of_correct_labels))
    length_of_list = len(list_of_predicted_labels_baseline)

    def boostrap_once():
        bootstrapped_data = []
        for i in range(length_of_list):
            ind_to_sample = int(length_of_list * random())
            if ind_to_sample == length_of_list:
                ind_to_sample -= 1
            bootstrapped_data.append(tups_to_draw_from[ind_to_sample])

        true_labels = [tup[2] for tup in bootstrapped_data]

        if num_labels == 2:
            average = 'binary'
        else:
            average = 'weighted'
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f1_baseline = f1_score(true_labels, [tup[1] for tup in bootstrapped_data], average=average)
            f1_roberta = f1_score(true_labels, [tup[0] for tup in bootstrapped_data], average=average)
        warnings.filterwarnings('default')

        return f1_roberta, f1_baseline

    list_of_bootstrapped_f1_tups = []
    for j in tqdm(range(num_times_to_bootstrap), total=num_times_to_bootstrap):
        list_of_bootstrapped_f1_tups.append(boostrap_once())

    with open(filename_to_write_data_to, 'w') as f:
        f.write('bootstrapped_f1_roberta,bootstrapped_f1_baseline\n')
        for roberta_val, baseline_val in list_of_bootstrapped_f1_tups:
            f.write(str(roberta_val) + ',' + str(baseline_val) + '\n')
    print('Wrote ' + filename_to_write_data_to)


def make_multilabel_csv(list_of_predicted_labels, actual_labels_as_list_of_ints, class_key_filename, csv_filename,
                        datasplit_label='test', using_ten_labels_instead = False):
    make_directories_as_necessary(csv_filename)
    precision_recall_f1_numtrulyinlabel_numguessedaslabel = \
        get_classwise_prec_rec_f1_numtrulyinlabel_numguessedaslabel(list_of_predicted_labels,
                                                                    actual_labels_as_list_of_ints)
    class_names = []
    with open(class_key_filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line != '':
                if ',' in line:
                    line = '"' + line + '"'
                class_names.append(line)
    if using_ten_labels_instead:
        class_names = ["J_Terrorism", "J_Intl-Domestic_Precedent", "J_Denial", "J_Political-Strategic",
                       "J_Development-Unity", "J_Legal_Procedure", "J_Emergency-Policy", "J_Law-and-order",
                       "J_Utilitarian-Deterrence", 'J_Combined']
    assert len(class_names) == len(precision_recall_f1_numtrulyinlabel_numguessedaslabel), \
        str(len(class_names)) + ', ' + str(len(precision_recall_f1_numtrulyinlabel_numguessedaslabel))

    with open(csv_filename, 'w') as f:
        f.write(','.join(['label_ind', 'str_label', 'num_of_each_class_in_' + datasplit_label, 'precision',
                          'recall', 'f1', 'num_guessed_as_class']) + '\n')
        for i in range(len(class_names)):
            fields_to_write = [str(i)]
            fields_to_write.append(class_names[i])
            fields_to_write.append(str(precision_recall_f1_numtrulyinlabel_numguessedaslabel[i][3]))
            fields_to_write.append(str(precision_recall_f1_numtrulyinlabel_numguessedaslabel[i][0]))
            fields_to_write.append(str(precision_recall_f1_numtrulyinlabel_numguessedaslabel[i][1]))
            fields_to_write.append(str(precision_recall_f1_numtrulyinlabel_numguessedaslabel[i][2]))
            fields_to_write.append(str(precision_recall_f1_numtrulyinlabel_numguessedaslabel[i][4]))
            f.write(','.join(fields_to_write) + '\n')
    print('Wrote ' + csv_filename)


def get_classwise_prec_rec_f1_numtrulyinlabel_numguessedaslabel(list_of_predicted_labels,
                                                                actual_labels_as_list_of_ints: List[int]):
    assert len(list_of_predicted_labels) == len(actual_labels_as_list_of_ints)
    precision_recall_f1_numtrulyinlabel_numguessedaslabel = []
    highest_label = max(max(list_of_predicted_labels), max(actual_labels_as_list_of_ints))
    for label in range(highest_label + 1):
        num_truly_in_label = actual_labels_as_list_of_ints.count(label)
        num_guessed_as_label = list_of_predicted_labels.count(label)
        true_guessed_positive = 0
        false_guessed_positive = 0
        for i in range(len(list_of_predicted_labels)):
            if list_of_predicted_labels[i] == label:
                if actual_labels_as_list_of_ints[i] == label:
                    true_guessed_positive += 1
                else:
                    false_guessed_positive += 1

        if true_guessed_positive + false_guessed_positive > 0:
            precision = true_guessed_positive / (true_guessed_positive + false_guessed_positive)
        else:
            precision = 'NaN'
        if num_truly_in_label > 0:
            recall = true_guessed_positive / num_truly_in_label
        else:
            recall = 'NaN'
        if recall == 'NaN' or precision == 'NaN' or (precision == 0 and recall == 0):
            f1 = 'NaN'
        else:
            f1 = 2 * precision * recall / (precision + recall)
        precision_recall_f1_numtrulyinlabel_numguessedaslabel.append((precision, recall, f1, num_truly_in_label,
                                                                      num_guessed_as_label))
    return precision_recall_f1_numtrulyinlabel_numguessedaslabel
