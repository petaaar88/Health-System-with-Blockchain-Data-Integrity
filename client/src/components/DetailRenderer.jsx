const DetailRenderer = ({ data, depth = 0, excludeFields = [] }) => {
  const formatFieldName = (key) => {
    return key
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const renderValue = (key, value, currentDepth) => {
    if (excludeFields.includes(key)) {
      return null;
    }

    const indentClass = `ml-${currentDepth * 4}`;
    
    if (value === null || value === undefined) {
      return (
        <div key={key} className={`mb-2 ${indentClass}`}>
          <span className="font-semibold text-gray-700">
            {formatFieldName(key)}:
          </span>{" "}
          <span className="text-gray-500 italic">N/A</span>
        </div>
      );
    }

    if (Array.isArray(value)) {
      return (
        <div key={key} className={`mb-3 ${indentClass}`}>
          <span className="font-semibold text-gray-700 block mb-1">
            {formatFieldName(key)}:
          </span>
          <div className="ml-4">
            {value.length === 0 ? (
              <span className="text-gray-500 italic">No items</span>
            ) : (
              value.map((item, index) => (
                <div key={index} className="mb-2 pl-2 border-l-2 border-gray-200">
                  <span className="text-sm text-gray-600 font-medium">
                    Item {index + 1}:
                  </span>
                  <DetailRenderer 
                    data={typeof item === 'object' ? item : { value: item }}
                    depth={currentDepth + 1}
                    excludeFields={excludeFields}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      );
    }

    if (value && typeof value === 'object') {
      return (
        <div key={key} className={`mb-3 ${indentClass}`}>
          <span className="font-semibold text-gray-700 block mb-2">
            {formatFieldName(key)}:
          </span>
          <div className="ml-4 pl-3 border-l-2 border-blue-200">
            <DetailRenderer 
              data={value} 
              depth={currentDepth + 1}
              excludeFields={excludeFields}
            />
          </div>
        </div>
      );
    }

    return (
      <div key={key} className={`mb-2 ${indentClass}`}>
        <span className="font-semibold text-gray-700">
          {formatFieldName(key)}:
        </span>{" "}
        <span className="text-gray-800">{String(value)}</span>
      </div>
    );
  };

  if (!data || typeof data !== 'object') {
    return null;
  }

  return (
    <div>
      {Object.entries(data).map(([key, value]) => 
        renderValue(key, value, depth)
      )}
    </div>
  );
};

export default DetailRenderer;