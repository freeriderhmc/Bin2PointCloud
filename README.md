## 2020-07-31

> panda dataset CCTV view

> nuscene data는 못쓸거같음

> 멀리 있는 차량 tracking에 문제가 있음. 코드를 고치는 데는 한계가 있을 듯함. 따라서 가까이서 끼여들기 data를 확보해야 한다.

> numbering이 바뀜.
  - 다른 차에 가려서 numbering이 바뀌는 경우
  
  - 두 차가 붙어버려서 예측값이 서로 바뀌는 경우
  
> Activate 기준 다시보기(현재는 5번 valid하면 activate == 1)

> class를 normal, lane_chng, turn으로 3가지로 나눔.


## 2020-08-03

> 43번째 프레임

  > kappa 값을 키움

  > gate 2의 width 값을 바꿈, length 값은 그대로

> 엉덩이만 나올 때 아직도 놓친다는 문제가 있음

> 106번째 프레임에서 sortCar가 계속 됐다 안됐다 하는 문제가 있음
  - ROI를 연결
  
  - clustering에서 z의 span을 줄임
