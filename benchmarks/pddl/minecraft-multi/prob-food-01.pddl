(define (problem minecraft-multi-20)

    (:domain minecraft-multi)

    (:objects
        steve01
    )

    (:init
        (hungry steve01)
        (= (total-cost) 0)
    )

    (:goal (and
        (feast-is-ready)
        (tribe-has-food)
    ))

    (:metric minimize
        (total-cost)
    )
)
