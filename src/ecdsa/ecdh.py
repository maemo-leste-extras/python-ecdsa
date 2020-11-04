"""
Class for performing Elliptic-curve Diffie-Hellman (ECDH) operations.
"""

from .util import number_to_string
from .ellipticcurve import INFINITY
from .keys import SigningKey, VerifyingKey


__all__ = [
    "ECDH",
    "NoKeyError",
    "NoCurveError",
    "InvalidCurveError",
    "InvalidSharedSecretError",
]


class NoKeyError(Exception):
    """ECDH. Key not found but it is needed for operation."""

    pass


class NoCurveError(Exception):
    """ECDH. Curve not set but it is needed for operation."""

    pass


class InvalidCurveError(Exception):
    """
    ECDH. Raised in case the public and private keys use different curves.
    """

    pass


class InvalidSharedSecretError(Exception):
    """ECDH. Raised in case the shared secret we obtained is an INFINITY."""

    pass


class ECDH(object):
    """
    Elliptic-curve Diffie-Hellman (ECDH). A key agreement protocol.

    Allows two parties, each having an elliptic-curve public-private key
    pair, to establish a shared secret over an insecure channel
    """

    def __init__(self, curve=None, private_key=None, public_key=None):
        """
        ECDH init.

        Call can be initialised without parameters, then the first operation
        (loading either key) will set the used curve.
        All parameters must be ultimately set before shared secret
        calculation will be allowed.

        :param curve: curve for operations
        :type curve: Curve
        :param private_key: `my` private key for ECDH
        :type private_key: SigningKey
        :param public_key:  `their` public key for ECDH
        :type public_key: VerifyingKey
        """
        self.curve = curve
        self.private_key = None
        self.public_key = None
        if private_key:
            self.load_private_key(private_key)
        if public_key:
            self.load_received_public_key(public_key)

    def _get_shared_secret(self, remote_public_key):
        if not self.private_key:
            raise NoKeyError(
                "Private key needs to be set to create shared secret"
            )
        if not self.public_key:
            raise NoKeyError(
                "Public key needs to be set to create shared secret"
            )
        if not (
            self.private_key.curve == self.curve == remote_public_key.curve
        ):
            raise InvalidCurveError(
                "Curves for public key and private key is not equal."
            )

        # shared secret = PUBKEYtheirs * PRIVATEKEYours
        result = (
            remote_public_key.pubkey.point
            * self.private_key.privkey.secret_multiplier
        )
        if result == INFINITY:
            raise InvalidSharedSecretError("Invalid shared secret (INFINITY).")

        return result.x()

    def set_curve(self, key_curve):
        """
        Set the working curve for ecdh operations.

        :param key_curve: curve from `curves` module
        :type key_curve: Curve
        """
        self.curve = key_curve

    def generate_private_key(self):
        """
        Generate local private key for ecdh operation with curve that was set.

        :raises NoCurveError: Curve must be set before key generation.

        :return: public (verifying) key from this private key.
        :rtype: VerifyingKey object
        """
        if not self.curve:
            raise NoCurveError("Curve must be set prior to key generation.")
        return self.load_private_key(SigningKey.generate(curve=self.curve))

    def load_private_key(self, private_key):
        """
        Load private key from SigningKey (keys.py) object.

        Needs to have the same curve as was set with set_curve method.
        If curve is not set - it sets from this SigningKey

        :param private_key: Initialised SigningKey class
        :type private_key: SigningKey

        :raises InvalidCurveError: private_key curve not the same as self.curve

        :return: public (verifying) key from this private key.
        :rtype: VerifyingKey object
        """
        if not self.curve:
            self.curve = private_key.curve
        if self.curve != private_key.curve:
            raise InvalidCurveError("Curve mismatch.")
        self.private_key = private_key
        return self.private_key.get_verifying_key()

    def load_private_key_bytes(self, private_key):
        """
        Load private key from byte string.

        Uses current curve and checks if the provided key matches
        the curve of ECDH key agreement.
        Key loads via from_string method of SigningKey class

        :param private_key: private key in bytes string format
        :type private_key: :term:`bytes-like object`

        :raises NoCurveError: Curve must be set before loading.

        :return: public (verifying) key from this private key.
        :rtype: VerifyingKey object
        """
        if not self.curve:
            raise NoCurveError("Curve must be set prior to key load.")
        return self.load_private_key(
            SigningKey.from_string(private_key, curve=self.curve)
        )

    def load_private_key_der(self, private_key_der):
        """
        Load private key from DER byte string.

        Compares the curve of the DER-encoded key with the ECDH set curve,
        uses the former if unset.

        Note, the only DER format supported is the RFC5915
        Look at keys.py:SigningKey.from_der()

        :param private_key_der: string with the DER encoding of private ECDSA
            key
        :type private_key_der: string

        :raises InvalidCurveError: private_key curve not the same as self.curve

        :return: public (verifying) key from this private key.
        :rtype: VerifyingKey object
        """
        return self.load_private_key(SigningKey.from_der(private_key_der))

    def load_private_key_pem(self, private_key_pem):
        """
        Load private key from PEM string.

        Compares the curve of the DER-encoded key with the ECDH set curve,
        uses the former if unset.

        Note, the only PEM format supported is the RFC5915
        Look at keys.py:SigningKey.from_pem()
        it needs to have `EC PRIVATE KEY` section

        :param private_key_pem: string with PEM-encoded private ECDSA key
        :type private_key_pem: string

        :raises InvalidCurveError: private_key curve not the same as self.curve

        :return: public (verifying) key from this private key.
        :rtype: VerifyingKey object
        """
        return self.load_private_key(SigningKey.from_pem(private_key_pem))

    def get_public_key(self):
        """
        Provides a public key that matches the local private key.

        Needs to be sent to the remote party.

        :return: public (verifying) key from local private key.
        :rtype: VerifyingKey object
       """
        return self.private_key.get_verifying_key()

    def load_received_public_key(self, public_key):
        """
        Load public key from VerifyingKey (keys.py) object.

        Needs to have the same curve as set as current for ecdh operation.
        If curve is not set - it sets it from VerifyingKey.

        :param public_key: Initialised VerifyingKey class
        :type public_key: VerifyingKey

        :raises InvalidCurveError: public_key curve not the same as self.curve
        """
        if not self.curve:
            self.curve = public_key.curve
        if self.curve != public_key.curve:
            raise InvalidCurveError("Curve mismatch.")
        self.public_key = public_key

    def load_received_public_key_bytes(self, public_key_str):
        """
        Load public key from byte string.

        Uses current curve and checks if key length corresponds to
        the current curve.
        Key loads via from_string method of VerifyingKey class

        :param public_key_str: public key in bytes string format
        :type public_key_str: :term:`bytes-like object`
        """
        return self.load_received_public_key(
            VerifyingKey.from_string(public_key_str, self.curve)
        )

    def load_received_public_key_der(self, public_key_der):
        """
        Load public key from DER byte string.

        Compares the curve of the DER-encoded key with the ECDH set curve,
        uses the former if unset.

        Note, the only DER format supported is the RFC5912
        Look at keys.py:VerifyingKey.from_der()

        :param public_key_der: string with the DER encoding of public ECDSA key
        :type public_key_der: string

        :raises InvalidCurveError: public_key curve not the same as self.curve
        """
        return self.load_received_public_key(
            VerifyingKey.from_der(public_key_der)
        )

    def load_received_public_key_pem(self, public_key_pem):
        """
        Load public key from PEM string.

        Compares the curve of the PEM-encoded key with the ECDH set curve,
        uses the former if unset.

        Note, the only PEM format supported is the RFC5912
        Look at keys.py:VerifyingKey.from_pem()

        :param public_key_pem: string with PEM-encoded public ECDSA key
        :type public_key_pem: string

        :raises InvalidCurveError: public_key curve not the same as self.curve
        """
        return self.load_received_public_key(
            VerifyingKey.from_pem(public_key_pem)
        )

    def generate_sharedsecret_bytes(self):
        """
        Generate shared secret from local private key and remote public key.

        The objects needs to have both private key and received public key
        before generation is allowed.

        :raises InvalidCurveError: public_key curve not the same as self.curve
        :raises NoKeyError: public_key or private_key is not set

        :return: shared secret
        :rtype: byte string
        """
        return number_to_string(
            self.generate_sharedsecret(), self.private_key.curve.order
        )

    def generate_sharedsecret(self):
        """
        Generate shared secret from local private key and remote public key.

        The objects needs to have both private key and received public key
        before generation is allowed.

        It's the same for local and remote party.
        shared secret(local private key, remote public key ) ==
                shared secret (local public key, remote private key)

        :raises InvalidCurveError: public_key curve not the same as self.curve
        :raises NoKeyError: public_key or private_key is not set

        :return: shared secret
        :rtype: int
        """
        return self._get_shared_secret(self.public_key)
