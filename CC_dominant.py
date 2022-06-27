import os
import shutil
import pickle
import cv2
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing.dummy
from multiprocessing.dummy import Process
from pathlib import Path
from collections import Counter
from sklearn.cluster import KMeans
from py_namethatcolor import get_color
from colorgroups import ColorGroups

# Convert dict to pickle (use when updating)
def cgroup_model_convert():
    CGroups_model = open(str((Path(__file__).parent).resolve())+'\\ColorGroups.pickle', 'wb')
    pickle.dump(ColorGroups, CGroups_model)

def img_path_check(img_name, input_path):
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    img_name = str(img_name)
    img_path = (input_path+f'\\{img_name}')
    if img_name.endswith(valid_extensions):
        return img_path
    else:
        return None

# Numerate files with the same name
def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path

def RGB2HEX(color):
    return "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))

def HEX2RGB(color):
    color = color.replace('#','')
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex[i:i+2], 16)
        rgb.append(decimal)
    return tuple(rgb)
 
def get_img(img_path):
    #Read unicode path (1d ndarr encode | 3d ndarr decode)
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    #BGR to RGB
    img_orig = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img_orig

def get_color_group(color_name):
    CGroups_model = open(str((Path(__file__).parent).resolve())+'\\ColorGroups.pickle', 'rb')
    CGroups_model_load = pickle.load(CGroups_model)

    for(color_group, colors) in CGroups_model_load.items():
        if(color_name.lower().replace(' ', '') in colors): 
            return color_group
    return color_name

def donut_chart(dict_to_plot, dict_closest_colors, temp_dir):
    # Set background/text color and size (1 - legend, 2 - figure, 3 - text)
    plt.rcParams.update({'axes.facecolor':'#5584b0'})
    plt.figure(facecolor='#c4e2ec', figsize = (10,8)) 
    # plt.rcParams['text.color'] = 'black'

    plot_labels = []
    plot_sizes = []
    for x, y in dict_to_plot.items():
        plot_labels.append(x)
        plot_sizes.append(y)

    explode = (0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1)
    exlode_index = len(explode)
    explode_index_decrement = 1
    
    while True:
        try:
            patches, labels, pct_texts = plt.pie(plot_sizes, labels = plot_labels, colors = dict_to_plot.keys(), autopct='%1.1f%%', startangle=90, pctdistance=0.55, explode=explode, rotatelabels =True)
            for label, pct_text in zip(labels, pct_texts):
                pct_text.set_rotation(label.get_rotation())
            break
        except Exception:
            # Decrease values if <10 colors
            explode = explode[0:exlode_index-explode_index_decrement]
            explode_index_decrement += 1
    # Convert dict to str for legend
    legend_list = []
    for elem in dict_closest_colors.values():
        legend_list.append(f'{elem[0]}: {elem[1]}')
    # Add circle for "Donut" chart
    centre_circle = plt.Circle((0,0),0.75,fc='#c4e2ec',linewidth=1.25)
    plt.gca().add_artist(centre_circle)
    plt.legend(legend_list, bbox_to_anchor=(1, 1), fontsize=9, title="Соседние цвета")
    plt.axis('equal')  
    plt.tight_layout()
    plt.savefig(str(temp_dir)+'\\Chart_temp_dom.png')
    img_path = str(temp_dir)+'\\Chart_temp_dom.png'
    return img_path

# Define the colors and (copy images / return path to chart)
def get_colors(img_path, no_of_colors, show_chart, output_path, temp_dir):
    img = get_img(img_path)
    # Reduce size to reduce the time
    mod_img = cv2.resize(img, (100, 50), interpolation = cv2.INTER_AREA)
    # Reduce img to 2D for KMeans
    mod_img = mod_img.reshape(mod_img.shape[0]*mod_img.shape[1], 3)

    # Define the clusters
    clust = KMeans(n_clusters = no_of_colors)
    labels = clust.fit_predict(mod_img)

    counts = Counter(labels)
    counts = dict(sorted(counts.items()))

    # Define colors in cluster centers
    center_colors = clust.cluster_centers_
    ordered_colors = [center_colors[i] for i in counts.keys()]
    hex_colors = [RGB2HEX(ordered_colors[i]) for i in counts.keys()]


    hex_colors_dict = dict(zip(hex_colors, list(counts.values()))) 
    sorted_hex_tuples = sorted(hex_colors_dict.items(), key=lambda item: item[1])
    sorted_hex_dict = {k: v for k, v in sorted_hex_tuples}

    # Define closest standard color name
    closest_color_name_result = []
    for elem in sorted_hex_dict:
        elem_name = get_color(elem).name
        closest_color_name_result.append(elem_name)    
    # Define color group
    color_group_result = []
    for elem in closest_color_name_result:
        color_group_result.append(get_color_group(elem))
    closest_color = dict(zip(list(sorted_hex_dict.keys()),list(zip(color_group_result,closest_color_name_result, sorted_hex_dict.values()))))

    # Get top 3 dominant colors
    color_list = []
    for key, value in reversed(closest_color.items()):
        color_list.append(value[0])
        if len(color_list) == 3: break
    color_list = list(set(color_list))

    if show_chart:
        # Return path to chart in temp directory
        return donut_chart(sorted_hex_dict, closest_color, temp_dir)
    else:
        # Copy images by pattern c1\c2-c3
        if len(color_list) == 3:
            path_to_images_1 = (output_path+f'\\{color_list[0]}\\{color_list[1]}-{color_list[2]}')
            path_to_images_2 = (output_path+f'\\{color_list[0]}\\{color_list[2]}-{color_list[1]}')
            isExist_1 = os.path.exists(path_to_images_1)
            isExist_2 = os.path.exists(path_to_images_2)
            if not isExist_1 and not isExist_2:
                os.makedirs(path_to_images_1)
                shutil.copy2(img_path, uniquify(path_to_images_1+f'\\{os.path.basename(img_path)}'))
                return
            if isExist_1:
                shutil.copy2(img_path, uniquify(path_to_images_1+f'\\{os.path.basename(img_path)}'))
                return
            if isExist_2:
                shutil.copy2(img_path, uniquify(path_to_images_2+f'\\{os.path.basename(img_path)}'))
                return

        if len(color_list) == 2:
            path_to_images = (output_path+f'\\{color_list[0]}\\{color_list[1]}')
            isExist = os.path.exists(path_to_images)
            if not isExist:
                os.makedirs(path_to_images)
                shutil.copy2(img_path, uniquify(path_to_images+f'\\{os.path.basename(img_path)}'))
            if isExist:
                shutil.copy2(img_path, uniquify(path_to_images+f'\\{os.path.basename(img_path)}'))
                return

        if len(color_list) == 1:
            path_to_images = (output_path+f'\\{color_list[0]}')
            isExist = os.path.exists(path_to_images)
            if not isExist:
                os.makedirs(path_to_images)
                shutil.copy2(img_path, uniquify(path_to_images+f'\\{os.path.basename(img_path)}'))
            if isExist:
                shutil.copy2(img_path, uniquify(path_to_images+f'\\{os.path.basename(img_path)}'))
                return
        

def start_dominant_colors(input_path, output_path, temp_dir, mode = 0):
    # mode 0 - sort; mode 1 - chart
    if mode == 0:
        multiprocessing.Semaphore(6)
        filenames_list = []
        for filename in os.listdir(input_path):
            path_image = img_path_check(filename, input_path)
            if path_image != None:
                p = Process(target=get_colors,args=(path_image, 10, False, output_path, temp_dir))
                p.start()
                filenames_list.append(p)
            else: continue
        for p in filenames_list:
            p.join()
    if mode == 1:
        path_image = img_path_check(os.path.basename(input_path), os.path.dirname(input_path))
        if path_image != None:
            return get_colors(path_image, 10, True, output_path, temp_dir)
        else: return