# -*- coding: utf-8 -*-


from hal_codec import HALCodec as OriginCodec

__all__ = ['HALCodec']

class HALCodec(OriginCodec):
    format = 'hal'

