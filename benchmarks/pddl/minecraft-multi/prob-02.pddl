(define (problem minecraft-multi-02)

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

    (:goal (and (tribe-has-food)))

)
