
class Queries:

  GET_PRODUCT_STEPS = """
    FOR phase IN Phase
      FILTER phase.product_key == @product_key
      RETURN {
        alias: phase.alias,
        phase_key: phase._key,
        steps: (
          FOR step IN Step
            FILTER step._key in phase.step_sequence
            return step
        )}
  """
