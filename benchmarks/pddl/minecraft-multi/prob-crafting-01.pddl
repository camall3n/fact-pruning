(define (problem minecraft-multi-01)

    (:domain minecraft-multi)

    (:objects
        alice bob carol steve
    )

    (:init
        (hungry alice)
        (hungry bob)
        (hungry carol)
        (hungry steve)
    )

    (:goal
        (and
            (hungry alice)
            (hungry bob)
            (hungry carol)
            (hungry steve)
            (has-wood-pickaxe alice)
            (has-stone-axe bob)
            (has-stone-pickaxe carol)
            (has-bed steve)
        )
    )

)
