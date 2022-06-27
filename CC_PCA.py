import os
import shutil
from clustimage import Clustimage
from matplotlib import pyplot as plt
from CC_dominant import uniquify

# Define min number of clusters (min images - 3)
def get_min_clust(count):
    if count >= 3 and count <= 10: count = 3
    if count > 10 and count <= 100:
        count = round((count/10)*0.8)
        if count < 3: count = 4
    if count > 100: 
        count = round(10 + (count/50))
    return count

def start_PCA(input_path, output_path, temp_dir):
    # Set parameters (dim (chart img size), n_components (number of components))
    cl = Clustimage(method='pca', dim=(160, 160), params_pca={'n_components': 80}, ext=['png', 'jpeg', 'jpg', 'webp'])#
    # Count valid images for clusterisation
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    count_clust = get_min_clust(len([f for f in os.listdir(input_path) if (os.path.join(input_path, f)).endswith(valid_extensions)]))
    # Import raw data (list of files)
    X = cl.import_data(input_path)
    # Extract features with PCA method (brightness, saturation)
    Xfeat = cl.extract_feat(X)
    # Embedding using tSNE
    cl.embedding(Xfeat)
    # Cluster settings
    cl.cluster(cluster='agglomerative', # agglomerative, kmeans, dbscan, hdbscan
                        evaluate='silhouette', # silhouette, dbindex, derivatives
                        metric='euclidean', # euclidean, hamming, cityblock, correlation, cosine, jaccard, mahalanobis, seuclidean, sqeuclidean
                        linkage='ward', # ward, single, complete, average, weighted, centroid, median
                        min_clust=count_clust, 
                        max_clust=round(count_clust*1.1)+1, 
                        cluster_space='high') # high, low
    # Make scatter chart
    cl.scatter(zoom=0.2, plt_all=True, figsize=(13,8), legend = True, args_scatter={'xlabel': '', 'ylabel': ''})
    plt.grid(False)
    plt.axis('off')
    plt.title('')
    plt.legend(['', ''])
    plt.gca().get_legend().remove()
    # Save chart to temp directory
    plt.savefig(str(temp_dir)+'\\Chart_temp_pca.png', transparent=True)
    img_path = str(temp_dir)+'\\Chart_temp_pca.png'
    # Move clusters (collections) of images
    for i in range(max(cl.results['labels'])+1):
        path_to_move = uniquify(output_path+f'\\Collection_{i}')
        isExist = os.path.exists(path_to_move)
        if not isExist: os.makedirs(path_to_move)
        # Label - cluster num
        label = i
        Iloc = cl.results['labels']==label
        pathnames = cl.results['pathnames'][Iloc]
        for elem in pathnames:       
            shutil.move(elem, path_to_move)
    # Return path to chart
    return img_path
