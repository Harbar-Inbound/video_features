import argparse

import torch

from utils.utils import form_list_from_user_input


def parallel_feature_extraction(args):
    '''Distributes the feature extraction in a embarasingly-parallel fashion. Specifically,
    it divides the dataset (list of video paths) among all specified devices evenly.'''

    if args.feature_type == 'i3d':
        from models.i3d.extract_i3d import ExtractI3D  # defined here to avoid import errors
        extractor = ExtractI3D(args)
    elif args.feature_type == 'vggish':
        if args.pytorch:
            from models.vggish_torch.extract_vggish import ExtractVGGish
            print("Using pytorch implementation!")
            extractor = ExtractVGGish(args)
        else:
            from models.vggish.extract_vggish import ExtractVGGish
            extractor = ExtractVGGish(args)

    # the indices correspond to the positions of the target videos in
    # the video_paths list. They are required here because
    # scatter module inputs only tensors but there is no such torch tensor
    # that would be suitable for strings (video_paths). Also, the
    # input have the method '.device' which allows us to access the
    # current device in the extractor.
    video_paths = form_list_from_user_input(args)
    if args.nocuda:
        print("Running without cuda support!")
        indices = torch.arange(len(video_paths), device='cpu')
        extractor.forward(indices)
    else:
        extractor.cuda()
        indices = torch.arange(len(video_paths))
        replicas = torch.nn.parallel.replicate(extractor, args.device_ids[:len(indices)])
        inputs = torch.nn.parallel.scatter(indices, args.device_ids[:len(indices)])
        torch.nn.parallel.parallel_apply(replicas[:len(inputs)], inputs)

    # closing the tqdm progress bar to avoid some unexpected errors due to multi-threading
    extractor.progress.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract Features')
    # Main args
    parser.add_argument('--feature_type', required=True, choices=['i3d', 'vggish'])
    parser.add_argument('--video_paths', nargs='+', help='space-separated paths to videos')
    parser.add_argument('--file_with_video_paths', help='.txt file where each line is a path')
    parser.add_argument('--device_ids', type=int, nargs='+', help='space-separated device ids')
    parser.add_argument('--tmp_path', default='./tmp',
                        help='folder to store the extracted frames before the extraction')
    parser.add_argument('--keep_frames', dest='keep_frames', action='store_true', default=False,
                        help='to keep frames after feature extraction')
    parser.add_argument('--on_extraction', default='print', choices=['print', 'save_numpy'],
                        help='what to do once the stack is extracted')
    parser.add_argument('--output_path', default='./output', help='where to store results if saved')
    # I3D options
    parser.add_argument('--pwc_path', default='./models/i3d/checkpoints/pwc_net.pt')
    parser.add_argument('--i3d_rgb_path', default='./models/i3d/checkpoints/i3d_rgb.pt')
    parser.add_argument('--i3d_flow_path', default='./models/i3d/checkpoints/i3d_flow.pt')
    parser.add_argument('--min_side_size', type=int, default=256, help='min(HEIGHT, WIDTH)')
    parser.add_argument('--extraction_fps', type=int, help='Do not specify for original video fps')
    parser.add_argument('--stack_size', type=int, default=64, help='Feature time span in fps')
    parser.add_argument('--step_size', type=int, default=64, help='Feature step size in fps')
    parser.add_argument(
        '--show_kinetics_pred', dest='show_kinetics_pred', action='store_true', default=False,
        help='to show the predictions of the i3d model into kinetics classes for each feature'
    )
    parser.add_argument('--kinetics_class_labels', default='./checkpoints/label_map.txt')
    # VGGish options
    parser.add_argument('--vggish_model_path', default='./models/{}/checkpoints/vggish_model.')
    parser.add_argument('--vggish_pca_path', default='./models/{}/checkpoints/vggish_postprocess.')

    parser.add_argument('--nocuda', dest='nocuda', action='store_true', help='When set, the experiments'
                                                                              'are run without CUDA support.')
    # Tensorflow or Pytorch implementation
    parser.add_argument('--pytorch', default=False,
                        help="Enable running with Pytorch, if not set, the default Tensorflow implementation is used.")
    args = parser.parse_args()

    # Interpolate path to have correct file extensions and submodule directory
    if '{}' in args.vggish_model_path:
        args.vggish_model_path = str(args.vggish_model_path).format(
            "vggish_torch" if args.pytorch else "vggish") + ("pt" if args.pytorch else "ckpt")
    if '{}' in args.vggish_pca_path:
        args.vggish_pca_path = str(args.vggish_pca_path).format("vggish_torch" if args.pytorch else "vggish") + (
            "pt" if args.pytorch else "npz")

    # some printing
    if args.on_extraction == 'save_numpy':
        print(f'Saving features to {args.output_path}')
    if args.keep_frames:
        print(f'Keeping temp files in {args.tmp_path}')

    parallel_feature_extraction(args)
