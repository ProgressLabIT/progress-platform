class Queries:

  SEARCH_POSITIONS = """
    FOR p IN Position

    LET search_match = @search ? LOWER(p.code) LIKE CONCAT('%', LOWER(@search), '%' p.code) : true

    LET parent_match = (
      @is_in_position
      ? COUNT(
        FOR parent IN 1..99 OUTBOUND p located_in
        PRUNE v._key == @is_in_position
        FILTER v._key == @is_in_position
        RETURN 1
      )
      : true
    )

    LET child_match = (
      @contains_position
      ? COUNT(
        FOR child IN 1..99 INBOUND p located_in
        PRUNE v._key == @contains_position
        FILTER v._key == @contains_position
        RETURN 1
      )
      : true
    )

    LET product_keys_match = (
      @has_product_key
      ? COUNT(
        FOR product, inventory IN 1..99 INBOUND p located_in
        PRUNE inventory._to == CONCAT('Product/', @has_product_key) && inventory.quantity > 0
        FILTER inventory._to == CONCAT('Product/', @has_product_key) && inventory.quantity > 0
        RETURN 1
      )
      : true
    )

    LET product_codes_match = (
      @has_product_code
      ? COUNT(
        FOR product, inventory IN 1..99 INBOUND p located_in
        PRUNE product.code == @has_product_code && inventory.quantity > 0
        FILTER product.code == @has_product_code && inventory.quantity > 0
        RETURN 1
      )
      : true


    FILTER search_match && parent_match && product_keys_match && product_codes_match

    LIMIT @offset, @limit || null

    RETURN p
  """
