from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import numpy as np
import tensorflow as tf
import random
from PIL import Image


from tensorflow.examples.tutorials.mnist import input_data


TF_DATA_DIR = os.getenv("TF_DATA_DIR", "/tmp/mnist/")
TF_MODEL_DIR = os.getenv("TF_MODEL_DIR", None)
TF_EXPORT_DIR = os.getenv("TF_EXPORT_DIR", "mnist/")
TF_MODEL_TYPE = os.getenv("TF_MODEL_TYPE", "GAN")
TF_TRAIN_STEPS = int(os.getenv("TF_TRAIN_STEPS", 300))
TF_BATCH_SIZE = int(os.getenv("TF_BATCH_SIZE", 100))
TF_LEARNING_RATE = float(os.getenv("TF_LEARNING_RATE", 0.01))


def model_inputs(real_dim, z_dim):
    inputs_real = tf.placeholder(tf.float32, (None, real_dim), name="inputs_real")
    inputs_z = tf.placeholder(tf.float32, (None, z_dim), name="inputs_z")

    return inputs_real, inputs_z


def generator(z, out_dim, n_units=128, reuse=False, alpha=0.01):
    with tf.variable_scope('generator', reuse=reuse):
        # Hidden layer
        h1 = tf.layers.dense(z, n_units, activation=None)
        # Leaky ReLU
        h1 = tf.maximum(h1, alpha * h1)

        # Logits and tanh output
        logits = tf.layers.dense(h1, out_dim, activation=None)
        out = tf.nn.tanh(logits)

        return out, logits


def discriminator(x, n_units=128, reuse=False, alpha=0.01):
    with tf.variable_scope('discriminator', reuse=reuse):
        # Hidden layer
        h1 = tf.layers.dense(x, n_units, activation=None)
        # Leaky ReLU
        h1 = tf.maximum(h1, alpha * h1)

        logits = tf.layers.dense(h1, 1, activation=None)
        out = tf.nn.sigmoid(logits)

        return out, logits


def main(unused_arguments):
    mnist = input_data.read_data_sets(TF_DATA_DIR, one_hot=True)
    input_size = 28 * 28
    z_size = 100
    g_hidden_size = 128
    d_hidden_size = 128
    alpha = 0.01
    smooth = 0.1
    tf.reset_default_graph()
    input_real, input_z = model_inputs(input_size, z_size)

    g_model, g_logits = generator(input_z, input_size, g_hidden_size, reuse=False, alpha=alpha)
    d_model_real, d_logits_real = discriminator(input_real, d_hidden_size, reuse=False, alpha=alpha)
    d_model_fake, d_logits_fake = discriminator(g_model, d_hidden_size, reuse=True, alpha=alpha)

    d_labels_real = tf.ones_like(d_logits_real) * (1 - smooth)
    d_labels_fake = tf.zeros_like(d_logits_fake)

    d_loss_real = tf.nn.sigmoid_cross_entropy_with_logits(labels=d_labels_real, logits=d_logits_real)
    d_loss_fake = tf.nn.sigmoid_cross_entropy_with_logits(labels=d_labels_fake, logits=d_logits_fake)

    d_loss = tf.reduce_mean(d_loss_real + d_loss_fake)

    g_loss = tf.reduce_mean(
        tf.nn.sigmoid_cross_entropy_with_logits(
            labels=tf.ones_like(d_logits_fake),
            logits=d_logits_fake))


    t_vars = tf.trainable_variables()
    g_vars = [var for var in t_vars if var.name.startswith("generator")]
    d_vars = [var for var in t_vars if var.name.startswith("discriminator")]

    d_train_opt = tf.train.AdamOptimizer().minimize(d_loss, var_list=d_vars)
    g_train_opt = tf.train.AdamOptimizer().minimize(g_loss, var_list=g_vars)

    batch_size = TF_BATCH_SIZE
    epochs = TF_TRAIN_STEPS
    samples = []
    losses = []

    export_path = os.path.join(
        tf.compat.as_bytes(TF_EXPORT_DIR),
        tf.compat.as_bytes(str(os.getpid()) + str(random.randint(1, 1000))))

    builder = tf.saved_model.builder.SavedModelBuilder(export_path)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        for e in range(epochs):
            for ii in range(mnist.train.num_examples // batch_size):
                batch = mnist.train.next_batch(batch_size)

                # Get images, reshape and rescale to pass to D
                batch_images = batch[0].reshape((batch_size, 784))
                batch_images = batch_images * 2 - 1

                # Sample random noise for G
                batch_z = np.random.uniform(-1, 1, size=(batch_size, z_size))

                # Run optimizers
                _ = sess.run(d_train_opt, feed_dict={input_real: batch_images, input_z: batch_z})
                _ = sess.run(g_train_opt, feed_dict={input_z: batch_z})

            # At the end of each epoch, get the losses and print them out
            train_loss_d = sess.run(d_loss, {input_z: batch_z, input_real: batch_images})
            train_loss_g = g_loss.eval({input_z: batch_z})

            print("Epoch {}/{}...".format(e + 1, epochs),
                  "Discriminator Loss: {:.4f}...".format(train_loss_d),
                  "Generator Loss: {:.4f}".format(train_loss_g))
            # Save losses to view after training
            losses.append((train_loss_d, train_loss_g))

            # Sample from generator as we're training for viewing afterwards
            sample_z = np.random.uniform(-1, 1, size=(16, z_size))
            gen_samples = sess.run(
                generator(input_z, input_size, reuse=True),
                feed_dict={input_z: sample_z})
            samples.append(gen_samples)

        test_vector = tf.placeholder(tf.float32, (None, z_size))
        tensor_info_zvector = tf.saved_model.utils.build_tensor_info(test_vector)
        #
        #         # gen_samples = sess.run(
        #         #     generator(test_vector, input_size, reuse=True),
        #         #     feed_dict={test_vector: test_vector.eval()}
        #         # )
        #
        sample = generator(test_vector, input_size, reuse=True)
        #         # extract the segmentation mask
        #         # output tensor info
        tensor_info_output = tf.saved_model.utils.build_tensor_info(tf.convert_to_tensor(sample[0]))
        prediction_signature = (
            tf.saved_model.signature_def_utils.build_signature_def(
                inputs={'zVector': tensor_info_zvector},
                outputs={'image': tensor_info_output},
                method_name=tf.saved_model.signature_constants.PREDICT_METHOD_NAME))

        builder.add_meta_graph_and_variables(
            sess, [tf.saved_model.tag_constants.SERVING],
            signature_def_map={
                'generated':
                    prediction_signature,
            })

        # export the model
        builder.save()

if __name__ == '__main__':
  tf.app.run()