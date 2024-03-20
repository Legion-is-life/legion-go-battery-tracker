(function (deckyFrontendLib, React) {
  'use strict';

  function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

  var React__default = /*#__PURE__*/_interopDefaultLegacy(React);

  var DefaultContext = {
    color: undefined,
    size: undefined,
    className: undefined,
    style: undefined,
    attr: undefined
  };
  var IconContext = React__default["default"].createContext && React__default["default"].createContext(DefaultContext);

  var __assign = window && window.__assign || function () {
    __assign = Object.assign || function (t) {
      for (var s, i = 1, n = arguments.length; i < n; i++) {
        s = arguments[i];
        for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
      }
      return t;
    };
    return __assign.apply(this, arguments);
  };
  var __rest = window && window.__rest || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0) t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function") for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
      if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i])) t[p[i]] = s[p[i]];
    }
    return t;
  };
  function Tree2Element(tree) {
    return tree && tree.map(function (node, i) {
      return React__default["default"].createElement(node.tag, __assign({
        key: i
      }, node.attr), Tree2Element(node.child));
    });
  }
  function GenIcon(data) {
    // eslint-disable-next-line react/display-name
    return function (props) {
      return React__default["default"].createElement(IconBase, __assign({
        attr: __assign({}, data.attr)
      }, props), Tree2Element(data.child));
    };
  }
  function IconBase(props) {
    var elem = function (conf) {
      var attr = props.attr,
        size = props.size,
        title = props.title,
        svgProps = __rest(props, ["attr", "size", "title"]);
      var computedSize = size || conf.size || "1em";
      var className;
      if (conf.className) className = conf.className;
      if (props.className) className = (className ? className + " " : "") + props.className;
      return React__default["default"].createElement("svg", __assign({
        stroke: "currentColor",
        fill: "currentColor",
        strokeWidth: "0"
      }, conf.attr, attr, svgProps, {
        className: className,
        style: __assign(__assign({
          color: props.color || conf.color
        }, conf.style), props.style),
        height: computedSize,
        width: computedSize,
        xmlns: "http://www.w3.org/2000/svg"
      }), title && React__default["default"].createElement("title", null, title), props.children);
    };
    return IconContext !== undefined ? React__default["default"].createElement(IconContext.Consumer, null, function (conf) {
      return elem(conf);
    }) : elem(DefaultContext);
  }

  // THIS FILE IS AUTO GENERATED
  function FaBatteryFull (props) {
    return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 640 512"},"child":[{"tag":"path","attr":{"d":"M544 160v64h32v64h-32v64H64V160h480m16-64H48c-26.51 0-48 21.49-48 48v224c0 26.51 21.49 48 48 48h512c26.51 0 48-21.49 48-48v-16h8c13.255 0 24-10.745 24-24V184c0-13.255-10.745-24-24-24h-8v-16c0-26.51-21.49-48-48-48zm-48 96H96v128h416V192z"}}]})(props);
  }

  // from https://medium.com/@pdx.lucasm/canvas-with-react-js-32e133c05258
  const Canvas = (props) => {
      const { draw, options, ...rest } = props;
      //const { context, ...moreConfig } = options;
      const canvasRef = useCanvas(draw);
      return window.SP_REACT.createElement("canvas", { ref: canvasRef, ...rest });
  };
  const useCanvas = (draw) => {
      const canvasRef = React.useRef(null);
      React.useEffect(() => {
          const canvas = canvasRef.current;
          const context = canvas.getContext('2d');
          let frameCount = 0;
          let animationFrameId;
          const render = () => {
              frameCount++;
              draw(context, frameCount);
              animationFrameId = window.requestAnimationFrame(render);
          };
          render();
          return () => {
              window.cancelAnimationFrame(animationFrameId);
          };
      }, [draw]);
      return canvasRef;
  };

  const Content = ({ serverAPI }) => {
      const [chargingGraphEnabled, setChargingGraphEnabled] = React.useState(false);
      const [powerPerAppEnabled, setPowerPerAppEnabled] = React.useState(true);
      const [lookback, setLookback] = React.useState(1);
      const [leData, setData] = React.useState();
      const [firstTime, setFirstTime] = React.useState(true);
      if (firstTime) {
          setFirstTime(false);
          serverAPI.callPluginMethod("get_recent_data", { lookback: lookback }).then((val) => { setData(val.result); });
      }
      const drawCanvas = async (ctx, frameCount) => {
          if (frameCount % 1000 > 1) {
              return;
          }
          if (leData == null) {
              var data = (await serverAPI.callPluginMethod("get_recent_data", { lookback: lookback })).result;
              console.log("Got first time data", data);
              setData(data);
          }
          else {
              var data = leData;
          }
          console.log("in draw canvas ", leData);
          const width = ctx.canvas.width;
          const height = ctx.canvas.height;
          ctx.strokeStyle = "#1a9fff";
          ctx.fillStyle = "#1a9fff";
          ctx.lineWidth = 2;
          ctx.lineJoin = "round";
          ctx.clearRect(0, 0, width, height);
          // graph helper lines
          ctx.beginPath();
          ctx.strokeStyle = "#093455";
          const totalLines = 7;
          const lineDistance = 1 / (totalLines + 1);
          for (let i = 1; i <= totalLines; i++) {
              ctx.moveTo(lineDistance * i * width, 0);
              ctx.lineTo(lineDistance * i * width, height);
              ctx.moveTo(0, lineDistance * i * height);
              ctx.lineTo(width, lineDistance * i * height);
          }
          ctx.stroke();
          ctx.beginPath();
          ctx.strokeStyle = "#1a9fff";
          ctx.fillStyle = "#1a9fff";
          // axis labels
          ctx.textAlign = "center";
          ctx.rotate(-Math.PI / 2);
          ctx.fillText("Batt %", -height / 2, 12); // Y axis is rotated 90 degrees
          ctx.rotate(Math.PI / 2);
          ctx.fillText("Time", width / 2, height - 4);
          // graph data labels
          ctx.textAlign = "start"; // default
          ctx.fillText(lookback, 2, height - 2);
          ctx.fillText("100%", 2, 9);
          ctx.textAlign = "right";
          ctx.fillText("Now", width - 2, height - 2);
          // ctx.moveTo(data[0].x/width, );
          for (var i = 0; i < data.x.length; i++) {
              ctx.beginPath();
              ctx.strokeStyle = data.strokeStyle[i];
              // console.log(data.x[i+1] - data.x[i]);
              /*if (data.x[i+1] - data.x[i] > 0.000078354119349755*10) {
                ctx.strokeStyle = "yellow";
              } else {
                if (data.cap[i+1] > data.cap[i]) {
                  ctx.strokeStyle = "green";
                } else {
                  ctx.strokeStyle = "rgba(153,0,0,0.1)";//"red";
                }
              }*/
              ctx.moveTo(data.x[i] * width, height); //height - data.cap[i]*height);
              ctx.lineTo(data.x[i] * width, height - data.cap[i] * height);
              //ctx.lineTo(data.x[i+1]*width, height- data.cap[i+1]*height);
              ctx.stroke();
          }
          console.debug("Rendered ", frameCount);
      };
      return (window.SP_REACT.createElement(deckyFrontendLib.PanelSection, null,
          window.SP_REACT.createElement(deckyFrontendLib.PanelSectionRow, null,
              window.SP_REACT.createElement(deckyFrontendLib.SliderField, { label: "Lookback in days", value: lookback || 1, step: 1, max: 7, min: 1, resetValue: 1, showValue: true, onChange: (value) => {
                      setLookback(value);
                      serverAPI.callPluginMethod("get_recent_data", { lookback: value }).then((val) => { setData(val.result); });
                  } })),
          window.SP_REACT.createElement(deckyFrontendLib.PanelSectionRow, null,
              window.SP_REACT.createElement(deckyFrontendLib.ToggleField, { label: "Battery charging history", checked: chargingGraphEnabled, onChange: (value) => {
                      setChargingGraphEnabled(value);
                  } })),
          chargingGraphEnabled &&
              window.SP_REACT.createElement(deckyFrontendLib.PanelSectionRow, null,
                  window.SP_REACT.createElement(Canvas, { draw: (ctx, frameCount) => drawCanvas(ctx, frameCount), width: 268, height: 150, style: {
                          "width": "268px",
                          "height": "150",
                          "padding": "0px",
                          "border": "1px solid #1a9fff",
                          "background-color": "#1a1f2c",
                          "border-radius": "4px",
                      }, onClick: (e) => console.log(e) })),
          window.SP_REACT.createElement(deckyFrontendLib.PanelSectionRow, null,
              window.SP_REACT.createElement(deckyFrontendLib.ToggleField, { label: "Per App Consumption", description: "Disable for Session Consumption", checked: powerPerAppEnabled, onChange: (value) => {
                      setPowerPerAppEnabled(value);
                  } })),
          powerPerAppEnabled &&
              window.SP_REACT.createElement(deckyFrontendLib.PanelSectionRow, null, leData != null && leData.power_data.map((item) => (
              //<div>{item.name}: {item.average_power}</div>
              window.SP_REACT.createElement(deckyFrontendLib.Field, { label: item.name }, item.average_power)))),
          !powerPerAppEnabled &&
              window.SP_REACT.createElement(deckyFrontendLib.PanelSectionRow, null, leData != null && leData.session_data.map((item) => (
              //<div>{item.name}: {item.average_power}</div>
              window.SP_REACT.createElement(deckyFrontendLib.Field, { label: item.name }, item.average_power))))));
  };
  var index = deckyFrontendLib.definePlugin((serverApi) => {
      console.log("defining battery plugin");
      var app = deckyFrontendLib.Router.MainRunningApp?.display_name;
      serverApi.callPluginMethod("set_app", { app: app });
      setInterval(() => {
          var app_now = deckyFrontendLib.Router.MainRunningApp?.display_name;
          serverApi.callPluginMethod("set_app", { app: app_now });
          app = app_now;
      }, 1000 * 10);
      return {
          title: window.SP_REACT.createElement("div", { className: deckyFrontendLib.staticClasses.Title }, "Example Plugin"),
          content: window.SP_REACT.createElement(Content, { serverAPI: serverApi }),
          icon: window.SP_REACT.createElement(FaBatteryFull, null),
          onDismount() {
              serverApi.routerHook.removeRoute("/decky-plugin-test");
          },
      };
  });

  return index;

})(DFL, SP_REACT);
