"""Self Attention and Intersample Attention blocks with TensorFlow"""

from typing import Callable, Dict, Iterable, Union
import tensorflow as tf

from .feedforward import FeedForwardNetwork


class TransformerBlock(tf.keras.layers.Layer):
    """_summary_

    Args:
        num_heads (int): _description_
        embed_dim (int): _description_
        hidden_dim (int): _description_
        dropout (float, optional): _description_.
            Defaults to 0.1.
        epsilon (float, optional): _description_.
            Defaults to 1e-6.
        kernel_initializer (Union[str, Callable], optional): _description_.
            Defaults to "glorot_uniform".
        bias_initializer (Union[str, Callable], optional): _description_.
            Defaults to "zeros".
        kernel_regularizer (Union[str, Callable], optional): _description_.
            Defaults to None.
        bias_regularizer (Union[str, Callable], optional): _description_.
            Defaults to None.
        activity_regularizer (Union[str, Callable], optional): _description_.
            Defaults to None.
        kernel_constraint (Union[str, Callable], optional): _description_.
            Defaults to None.
        bias_constraint (Union[str, Callable], optional): _description_.
            Defaults to None.
    """

    def __init__(
        self,
        num_heads: int,
        embed_dim: int,
        hidden_dim: int,
        dropout: float = 0.1,
        epsilon: float = 1e-6,
        kernel_initializer: Union[str, Callable] = "glorot_uniform",
        bias_initializer: Union[str, Callable] = "zeros",
        kernel_regularizer: Union[str, Callable] = None,
        bias_regularizer: Union[str, Callable] = None,
        activity_regularizer: Union[str, Callable] = None,
        kernel_constraint: Union[str, Callable] = None,
        bias_constraint: Union[str, Callable] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Transformer/Attention block hyperparameters
        self.num_heads = num_heads
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim

        self.epsilon = epsilon
        self.dropout = dropout

        # Trainable weights
        self.kernel_initializer = tf.keras.initializers.get(kernel_initializer)
        self.bias_initializer = tf.keras.initializers.get(bias_initializer)
        self.kernel_regularizer = tf.keras.regularizers.get(kernel_regularizer)
        self.bias_regularizer = tf.keras.regularizers.get(bias_regularizer)
        self.activity_regularizer = tf.keras.regularizers.get(activity_regularizer)
        self.kernel_constraint = tf.keras.constraints.get(kernel_constraint)
        self.bias_constraint = tf.keras.constraints.get(bias_constraint)

    def build(self, input_shape: Union[tf.TensorShape, Iterable[tf.TensorShape]]):
        # Defining Transformer block layers
        self.attention_layer = tf.keras.layers.MultiHeadAttention(
            num_heads=self.num_heads,
            key_dim=self.embed_dim,
            dropout=self.dropout,
            use_bias=True,
            kernel_initializer=self.kernel_initializer,
            bias_initializer=self.bias_initializer,
            kernel_regularizer=self.kernel_regularizer,
            bias_regularizer=self.bias_regularizer,
            activity_regularizer=self.activity_regularizer,
            kernel_constraint=self.kernel_constraint,
            bias_constraint=self.bias_constraint,
        )

        self.feed_forward_network = FeedForwardNetwork(
            hidden_dim=self.hidden_dim,
            output_dim=self.embed_dim,
            hidden_activation=tf.nn.gelu,
            output_activation=tf.nn.gelu,
            kernel_initializer=self.kernel_initializer,
            bias_initializer=self.bias_initializer,
            kernel_regularizer=self.kernel_regularizer,
            bias_regularizer=self.bias_regularizer,
            activity_regularizer=self.activity_regularizer,
            kernel_constraint=self.kernel_constraint,
            bias_constraint=self.bias_constraint,
        )

        self.layer_norm1 = tf.keras.layers.LayerNormalization(epsilon=self.epsilon)
        self.layer_norm2 = tf.keras.layers.LayerNormalization(epsilon=self.epsilon)

        self.dropout1 = tf.keras.layers.Dropout(rate=self.dropout)
        self.dropout2 = tf.keras.layers.Dropout(rate=self.dropout)

        super().build(input_shape)

    def call(self, inputs: tf.Tensor, training: bool, mask: tf.Tensor) -> tf.Tensor:
        """[summary]

        Args:
            inputs (tf.Tensor): [description]
            training (bool): [description]
            mask (tf.Tensor): [description]

        Returns:
            tf.Tensor: [description]
        """
        attention_output = self.compute_attention(
            inputs, training=training, attention_mask=mask
        )
        attention_output = self.dropout1(attention_output, training=training)
        output1 = self.layer_norm1(inputs + attention_output)

        output2 = self.feed_forward_network(output1)
        output2 = self.dropout2(output2, training=training)

        return self.layer_norm2(output1 + output2)

    def compute_attention(
        self, inputs: tf.Tensor, training: bool, attention_mask: tf.Tensor
    ) -> tf.Tensor:
        return self.attention_layer(
            inputs, inputs, training=training, attention_mask=attention_mask
        )

    @classmethod
    def from_config(cls, config: Dict):
        config["kernel_initializer"] = tf.keras.initializers.deserialize(
            config["kernel_initializer"]
        )
        config["bias_initializer"] = tf.keras.initializers.deserialize(
            config["bias_initializer"]
        )
        config["kernel_regularizer"] = tf.keras.regularizers.deserialize(
            config["kernel_regularizer"]
        )
        config["bias_regularizer"] = tf.keras.regularizers.deserialize(
            config["bias_regularizer"]
        )
        config["activity_regularizer"] = tf.keras.regularizers.deserialize(
            config["activity_regularizer"]
        )
        config["kernel_constraint"] = tf.keras.constraints.deserialize(
            config["kernel_constraint"]
        )
        config["bias_constraint"] = tf.keras.constraints.deserialize(
            config["bias_constraint"]
        )
        return cls(**config)

    def get_config(self) -> dict:
        base_config = super().get_config()
        config = {
            "num_heads": self.num_heads,
            "embed_dim": self.embed_dim,
            "hidden_dim": self.hidden_dim,
            "dropout": self.dropout,
            "epsilon": self.epsilon,
            "kernel_initializer": tf.keras.initializers.serialize(
                self.kernel_initializer
            ),
            "bias_initializer": tf.keras.initializers.serialize(self.bias_initializer),
            "kernel_regularizer": self.tf.keras.regularizers.serialize(
                self.kernel_regularizer
            ),
            "bias_regularizer": self.tf.keras.regularizers.serialize(
                self.bias_regularizer
            ),
            "activity_regularizer": self.tf.keras.regularizers.serialize(
                self.activity_regularizer
            ),
            "kernel_constraint": self.tf.keras.constraints.serialize(
                self.kernel_constraint
            ),
            "bias_constraint": self.tf.keras.constraints.serialize(
                self.bias_constraint
            ),
        }
        return dict(list(base_config.items()) + list(config.items()))


class IntersampleTransformerBlock(TransformerBlock):
    """_summary_

    Args:
        num_heads (int): _description_
        embed_dim (int): _description_
        hidden_dim (int): _description_
        dropout (float, optional): _description_.
            Defaults to 0.1.
        epsilon (float, optional): _description_.
            Defaults to 1e-6.
        kernel_initializer (Union[str, Callable], optional): _description_.
            Defaults to "glorot_uniform".
        bias_initializer (Union[str, Callable], optional): _description_.
            Defaults to "zeros".
        kernel_regularizer (Union[str, Callable], optional): _description_.
            Defaults to None.
        bias_regularizer (Union[str, Callable], optional): _description_.
            Defaults to None.
        activity_regularizer (Union[str, Callable], optional): _description_.
            Defaults to None.
        kernel_constraint (Union[str, Callable], optional): _description_.
            Defaults to None.
        bias_constraint (Union[str, Callable], optional): _description_.
            Defaults to None.
    """

    def compute_attention(
        self, inputs: tf.Tensor, training: bool, attention_mask: tf.Tensor
    ) -> tf.Tensor:
        """Intersample Attention operation.

        Args:
            inputs (tf.Tensor): [description]
            training (bool): [description]
            attention_mask (tf.Tensor): [description]

        Returns:
            tf.Tensor: [description]
        """
        batch, n_features, feature_dim = tf.shape(inputs)
        reshaped_inputs = tf.reshape(inputs, (1, batch, n_features * feature_dim))

        attention_output = self.attention_layer(
            reshaped_inputs,
            reshaped_inputs,
            training=training,
            attention_mask=attention_mask,
        )
        output = tf.reshape(attention_output, (batch, n_features, feature_dim))
        return output